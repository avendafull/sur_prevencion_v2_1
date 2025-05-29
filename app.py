from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Cliente, Cotizacion, Finanzas, Pensionista, GastoExtra
from datetime import datetime
import pandas as pd
import io
from collections import defaultdict

# --- Configuración principal
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.template_filter('format_miles')
def format_miles(value):
    try:
        return '{:,.0f}'.format(float(value)).replace(',', '.')
    except:
        return value

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------ LOGIN / LOGOUT --------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    clientes_count = Cliente.query.count()
    cotizaciones_count = Cotizacion.query.count()
    pensionistas_count = Pensionista.query.count()

    ingresos = db.session.query(db.func.coalesce(db.func.sum(Finanzas.monto), 0)).filter_by(tipo='ingreso').scalar()
    egresos_pagados = db.session.query(db.func.coalesce(db.func.sum(Finanzas.monto), 0)).filter_by(tipo='egreso', estado_pago='Pagado').scalar()
    egresos_pendientes = db.session.query(db.func.coalesce(db.func.sum(Finanzas.monto), 0)).filter_by(tipo='egreso', estado_pago='Pendiente').scalar()

    saldo_total = ingresos - egresos_pagados

    return render_template(
        'dashboard.html',
        clientes_count=clientes_count,
        cotizaciones_count=cotizaciones_count,
        ingresos=ingresos,
        egresos_pagados=egresos_pagados,
        egresos_pendientes=egresos_pendientes,
        pensionistas_count=pensionistas_count,
        saldo_total=saldo_total
    )

# ----------- CRUD CLIENTES -----------
@app.route('/clientes')
@login_required
def clientes():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def cliente_nuevo():
    if request.method == 'POST':
        nombre = request.form['nombre']
        rut = request.form['rut']
        contacto = request.form['contacto']
        direccion = request.form['direccion']
        nuevo_cliente = Cliente(nombre=nombre, rut=rut, contacto=contacto, direccion=direccion)
        db.session.add(nuevo_cliente)
        db.session.commit()
        flash('Cliente creado con éxito.', 'success')
        return redirect(url_for('clientes'))
    return render_template('clientes_form.html', cliente=None)

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def cliente_editar(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nombre = request.form['nombre']
        cliente.rut = request.form['rut']
        cliente.contacto = request.form['contacto']
        cliente.direccion = request.form['direccion']
        db.session.commit()
        flash('Cliente actualizado con éxito.', 'success')
        return redirect(url_for('clientes'))
    return render_template('clientes_form.html', cliente=cliente)

@app.route('/clientes/borrar/<int:id>')
@login_required
def cliente_borrar(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado.', 'info')
    return redirect(url_for('clientes'))

# ----------- CRUD PENSIONISTAS -----------
@app.route('/pensionistas')
@login_required
def pensionistas():
    pensionistas = Pensionista.query.all()
    return render_template('pensionistas.html', pensionistas=pensionistas)

@app.route('/pensionistas/nuevo', methods=['GET', 'POST'])
@login_required
def pensionistas_form():
    if request.method == 'POST':
        nombre = request.form['nombre']
        empresa = request.form['empresa']
        habitacion = request.form['habitacion']
        fecha_ingreso = request.form['fecha_ingreso']
        monto_mensual = request.form['monto_mensual']

        nuevo = Pensionista(
            nombre=nombre,
            empresa=empresa,
            habitacion=habitacion,
            fecha_ingreso=datetime.strptime(fecha_ingreso, "%Y-%m-%d"),
            monto_mensual=float(monto_mensual)
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Pensionista agregado con éxito.', 'success')
        return redirect(url_for('pensionistas'))
    return render_template('pensionistas_form.html')

@app.route('/pensionistas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def pensionista_editar(id):
    pensionista = Pensionista.query.get_or_404(id)
    if request.method == 'POST':
        pensionista.nombre = request.form['nombre']
        pensionista.empresa = request.form['empresa']
        pensionista.habitacion = request.form['habitacion']
        pensionista.monto_mensual = request.form['monto_mensual'] or 0
        fecha_ingreso_str = request.form['fecha_ingreso'] or None
        pensionista.fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%Y-%m-%d').date() if fecha_ingreso_str else None
        db.session.commit()
        flash('Pensionista actualizado con éxito.', 'success')
        return redirect(url_for('pensionistas'))
    return render_template('pensionistas_form.html', pensionista=pensionista)

@app.route('/pensionistas/borrar/<int:id>')
@login_required
def pensionista_borrar(id):
    pensionista = Pensionista.query.get_or_404(id)
    db.session.delete(pensionista)
    db.session.commit()
    flash('Pensionista eliminado.', 'info')
    return redirect(url_for('pensionistas'))

# ----------- GASTOS EXTRA / PEDIDOS ADICIONALES -----------
@app.route('/gastos_extra/<int:pensionista_id>', methods=['GET', 'POST'])
@login_required
def gastos_extra(pensionista_id):
    pensionista = Pensionista.query.get_or_404(pensionista_id)
    hoy = datetime.now()

    # Filtros de fecha
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str or not end_date_str:
        start_date = datetime(hoy.year, hoy.month, 1).date()
        if hoy.month == 12:
            end_date = datetime(hoy.year + 1, 1, 1).date()
        else:
            end_date = datetime(hoy.year, hoy.month + 1, 1).date()
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
    else:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    # Debug de fechas (puedes quitarlo después)
    print("FECHAS FILTRO:", start_date, end_date, "FECHAS REGISTRO:", [g.fecha for g in pensionista.gastos_extra])

    gastos_rango = [
        g for g in pensionista.gastos_extra
        if g.fecha and start_date <= (g.fecha.date() if hasattr(g.fecha, "date") else g.fecha) <= end_date
    ]
    total_rango = sum(float(g.monto) for g in gastos_rango)

    resumen_por_dia = defaultdict(float)
    for g in gastos_rango:
        fecha_str = g.fecha.strftime('%d/%m/%Y') if hasattr(g.fecha, "strftime") else str(g.fecha)
        resumen_por_dia[fecha_str] += float(g.monto)

    return render_template(
        'gastos_extra.html',
        pensionista=pensionista,
        gastos_mes=gastos_rango,
        total_mes=total_rango,
        resumen_por_dia=resumen_por_dia,
        selected_start_date=start_date_str,
        selected_end_date=end_date_str
    )

@app.route('/gastos_extra/nuevo/<int:pensionista_id>', methods=['GET', 'POST'])
@login_required
def gasto_extra_form(pensionista_id):
    pensionista = Pensionista.query.get_or_404(pensionista_id)
    if request.method == 'POST':
        fecha = request.form['fecha']
        descripcion = request.form['descripcion']
        monto = request.form['monto']

        nuevo_gasto = GastoExtra(
            pensionista_id=pensionista.id,
            fecha=datetime.strptime(fecha, "%Y-%m-%d"),
            descripcion=descripcion,
            monto=float(monto)
        )
        db.session.add(nuevo_gasto)
        db.session.commit()
        flash('Pedido adicional registrado.', 'success')
        return redirect(url_for('gastos_extra', pensionista_id=pensionista.id))
    return render_template('gastos_extra_form.html', pensionista=pensionista)

@app.route('/gastos_extra/editar/<int:gasto_id>', methods=['GET', 'POST'])
@login_required
def gasto_extra_editar(gasto_id):
    gasto = GastoExtra.query.get_or_404(gasto_id)
    pensionista = Pensionista.query.get_or_404(gasto.pensionista_id)
    if request.method == 'POST':
        gasto.descripcion = request.form['descripcion']
        gasto.monto = request.form['monto']
        fecha_str = request.form['fecha'] or None
        gasto.fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        db.session.commit()
        flash('Gasto extra actualizado', 'success')
        return redirect(url_for('gastos_extra', pensionista_id=pensionista.id))
    return render_template('gastos_extra_form.html', pensionista=pensionista, gasto=gasto)

@app.route('/gastos_extra/borrar/<int:gasto_id>')
@login_required
def gasto_extra_borrar(gasto_id):
    gasto = GastoExtra.query.get_or_404(gasto_id)
    pensionista_id = gasto.pensionista_id
    db.session.delete(gasto)
    db.session.commit()
    flash('Gasto extra eliminado', 'info')
    return redirect(url_for('gastos_extra', pensionista_id=pensionista_id))

@app.route('/gastos_extra/exportar_excel/<int:pensionista_id>')
@login_required
def exportar_gastos_excel(pensionista_id):
    pensionista = Pensionista.query.get_or_404(pensionista_id)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    hoy = datetime.now()
    if not start_date_str or not end_date_str:
        start_date = datetime(hoy.year, hoy.month, 1).date()
        if hoy.month == 12:
            end_date = datetime(hoy.year + 1, 1, 1).date()
        else:
            end_date = datetime(hoy.year, hoy.month + 1, 1).date()
    else:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    gastos_rango = [
        g for g in pensionista.gastos_extra
        if g.fecha and start_date <= (g.fecha.date() if hasattr(g.fecha, "date") else g.fecha) <= end_date
    ]

    data = [{
        "Fecha": g.fecha.strftime('%d/%m/%Y') if g.fecha else '',
        "Descripción": g.descripcion,
        "Monto": g.monto
    } for g in gastos_rango]

    df = pd.DataFrame(data)
    resumen = df.groupby("Fecha")["Monto"].sum().reset_index().rename(columns={"Monto": "Total del Día"})
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Pedidos', index=False)
        resumen.to_excel(writer, sheet_name='Resumen por Día', index=False)
    output.seek(0)

    nombre_archivo = f"pedidos_{pensionista.nombre}_{start_date_str}_a_{end_date_str}.xlsx".replace(" ", "_")
    return send_file(output, as_attachment=True, download_name=nombre_archivo, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ----------- CRUD COTIZACIONES -----------
@app.route('/cotizaciones')
@login_required
def cotizaciones():
    cotizaciones = Cotizacion.query.all()
    return render_template('cotizaciones.html', cotizaciones=cotizaciones)

@app.route('/cotizaciones/nueva', methods=['GET', 'POST'])
@login_required
def cotizacion_nueva():
    clientes = Cliente.query.all()
    if request.method == 'POST':
        fecha = request.form['fecha'] or None
        monto = request.form['monto']
        cliente_id = request.form['cliente_id']
        estado = request.form['estado']
        nueva_cot = Cotizacion(fecha=fecha, monto=monto, cliente_id=cliente_id, estado=estado)
        db.session.add(nueva_cot)
        db.session.commit()
        flash('Cotización creada con éxito.', 'success')
        return redirect(url_for('cotizaciones'))
    return render_template('cotizaciones_form.html', cotizacion=None, clientes=clientes)

@app.route('/cotizaciones/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def cotizacion_editar(id):
    cotizacion = Cotizacion.query.get_or_404(id)
    clientes = Cliente.query.all()
    if request.method == 'POST':
        cotizacion.fecha = request.form['fecha'] or None
        cotizacion.monto = request.form['monto']
        cotizacion.cliente_id = request.form['cliente_id']
        cotizacion.estado = request.form['estado']
        db.session.commit()
        flash('Cotización actualizada con éxito.', 'success')
        return redirect(url_for('cotizaciones'))
    return render_template('cotizaciones_form.html', cotizacion=cotizacion, clientes=clientes)

@app.route('/cotizaciones/borrar/<int:id>')
@login_required
def cotizacion_borrar(id):
    cotizacion = Cotizacion.query.get_or_404(id)
    db.session.delete(cotizacion)
    db.session.commit()
    flash('Cotización eliminada.', 'info')
    return redirect(url_for('cotizaciones'))

# ----------- CRUD FINANZAS -----------
@app.route('/finanzas')
@login_required
def finanzas():
    finanzas = Finanzas.query.all()
    return render_template('finanzas.html', finanzas=finanzas)

@app.route('/finanzas/nueva', methods=['GET', 'POST'])
@login_required
def finanza_nueva():
    pensionistas = Pensionista.query.all()
    if request.method == 'POST':
        tipo = request.form['tipo']
        recibido_de = request.form.get('recibido_de') if tipo == 'ingreso' else None
        estado_pago = request.form.get('estado_pago') if tipo == 'egreso' else "Pagado"
        concepto = request.form['concepto']
        monto = request.form['monto']
        fecha_str = request.form['fecha'] or None
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        pensionista_id = request.form.get('pensionista_id') or None
        if not pensionista_id:
            pensionista_id = None
        nueva_fin = Finanzas(
            tipo=tipo,
            recibido_de=recibido_de,
            estado_pago=estado_pago,
            concepto=concepto,
            monto=monto,
            fecha=fecha,
            pensionista_id=pensionista_id
        )
        db.session.add(nueva_fin)
        db.session.commit()
        flash('Movimiento financiero creado con éxito.', 'success')
        return redirect(url_for('finanzas'))
    return render_template('finanzas_form.html', finanza=None, pensionistas=pensionistas)

@app.route('/finanzas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def finanza_editar(id):
    finanza = Finanzas.query.get_or_404(id)
    pensionistas = Pensionista.query.all()
    if request.method == 'POST':
        tipo = request.form['tipo']
        finanza.tipo = tipo
        finanza.recibido_de = request.form.get('recibido_de') if tipo == 'ingreso' else None
        finanza.estado_pago = request.form.get('estado_pago') if tipo == 'egreso' else "Pagado"
        finanza.concepto = request.form['concepto']
        finanza.monto = request.form['monto']
        fecha_str = request.form['fecha'] or None
        finanza.fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        finanza.pensionista_id = request.form.get('pensionista_id') or None
        if not finanza.pensionista_id:
            finanza.pensionista_id = None
        db.session.commit()
        flash('Movimiento financiero actualizado.', 'success')
        return redirect(url_for('finanzas'))
    return render_template('finanzas_form.html', finanza=finanza, pensionistas=pensionistas)

@app.route('/finanzas/borrar/<int:id>')
@login_required
def finanza_borrar(id):
    finanza = Finanzas.query.get_or_404(id)
    db.session.delete(finanza)
    db.session.commit()
    flash('Movimiento financiero eliminado.', 'info')
    return redirect(url_for('finanzas'))

@app.route('/finanzas/marcar_pagado/<int:id>', methods=['POST'])
@login_required
def marcar_pagado(id):
    movimiento = Finanzas.query.get_or_404(id)
    if movimiento.tipo == 'egreso' and movimiento.estado_pago == 'Pendiente':
        movimiento.estado_pago = 'Pagado'
        db.session.commit()
    return redirect(request.referrer or url_for('finanzas'))

# ---- INICIALIZACIÓN DE BASE Y USUARIOS DEMO ----
if __name__ == '__main__':
    print("Rutas disponibles:")
    for rule in app.url_map.iter_rules():
        print(rule)
    with app.app_context():
        db.create_all()
        # Crear usuarios demo si no existen
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='admin123', role='admin')
            db.session.add(admin)
            db.session.commit()
        if not User.query.filter_by(username='operador').first():
            operador = User(username='operador', password='operador123', role='operador')
            db.session.add(operador)
            db.session.commit()
    app.run(debug=True)
