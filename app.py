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

# --- Filtro moneda CLP ---
@app.template_filter('format_miles')
def format_miles(value):
    try:
        return '$ {:,.0f}'.format(float(value)).replace(',', '.')
    except:
        return value

# --- Login Manager ---
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== AUTENTICACIÓN ====================

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

# ==================== DASHBOARD ====================

@app.route('/')
@login_required
def dashboard():
    clientes_count = Cliente.query.count()
    cotizaciones_count = Cotizacion.query.count()
    pensionistas_count = Pensionista.query.count()
    ingresos = db.session.query(db.func.coalesce(db.func.sum(Finanzas.monto), 0)).filter_by(tipo='ingreso').scalar() or 0
    egresos_pagados = db.session.query(db.func.coalesce(db.func.sum(Finanzas.monto), 0)).filter(Finanzas.tipo=='egreso', Finanzas.pagado==True).scalar() or 0
    egresos_pendientes = db.session.query(db.func.coalesce(db.func.sum(Finanzas.monto), 0)).filter(Finanzas.tipo=='egreso', Finanzas.pagado==False).scalar() or 0
    saldo_total = ingresos - egresos_pagados

    # --- Deuda por proveedor ---
    deudas_proveedores = db.session.query(
        Finanzas.proveedor,
        db.func.sum(Finanzas.monto)
    ).filter(
        Finanzas.tipo == 'egreso',
        Finanzas.forma_pago == 'credito',
        Finanzas.pagado == False,
        Finanzas.proveedor != None
    ).group_by(Finanzas.proveedor).all()

    return render_template(
        'dashboard.html',
        clientes_count=clientes_count,
        cotizaciones_count=cotizaciones_count,
        ingresos=ingresos,
        egresos_pagados=egresos_pagados,
        egresos_pendientes=egresos_pendientes,
        pensionistas_count=pensionistas_count,
        saldo_total=saldo_total,
        deudas_proveedores=deudas_proveedores
    )

# ==================== CRUD CLIENTES ====================

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

# ==================== CRUD PENSIONISTAS ====================

@app.route('/pensionistas')
@login_required
def pensionistas():
    pensionistas = Pensionista.query.order_by(Pensionista.nombre).all()
    return render_template('pensionistas.html', pensionistas=pensionistas)

@app.route('/pensionistas/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_pensionista():
    if request.method == 'POST':
        nombre = request.form['nombre']
        empresa = request.form['empresa']
        habitacion = request.form['habitacion']
        fecha_ingreso = request.form['fecha_ingreso']
        monto_mensual = request.form['monto_mensual']
        costo_alimentacion = request.form['costo_alimentacion']
        pensionista = Pensionista(
            nombre=nombre,
            empresa=empresa,
            habitacion=habitacion,
            fecha_ingreso=datetime.strptime(fecha_ingreso, '%Y-%m-%d'),
            monto_mensual=float(monto_mensual),
            costo_alimentacion=float(costo_alimentacion)
        )
        db.session.add(pensionista)
        db.session.commit()
        flash('Pensionista agregado correctamente', 'success')
        return redirect(url_for('pensionistas'))
    return render_template('pensionistas_form.html', pensionista=None)

@app.route('/pensionistas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_pensionista(id):
    pensionista = Pensionista.query.get_or_404(id)
    if request.method == 'POST':
        pensionista.nombre = request.form['nombre']
        pensionista.empresa = request.form['empresa']
        pensionista.habitacion = request.form['habitacion']
        fecha_ingreso = request.form['fecha_ingreso']
        pensionista.fecha_ingreso = datetime.strptime(fecha_ingreso, '%Y-%m-%d')
        pensionista.monto_mensual = float(request.form['monto_mensual'])
        pensionista.costo_alimentacion = float(request.form['costo_alimentacion'])
        db.session.commit()
        flash('Pensionista actualizado correctamente', 'success')
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

# ==================== CRUD GASTOS EXTRA ====================

@app.route('/gastos_extra/<int:pensionista_id>', methods=['GET', 'POST'])
@login_required
def gastos_extra(pensionista_id):
    pensionista = Pensionista.query.get_or_404(pensionista_id)
    hoy = datetime.now()
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

# ----------- GASTOS EXTRA / PEDIDOS ADICIONALES -----------

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
    # Nuevo: pasa gasto=None al crear
    return render_template('gastos_extra_form.html', pensionista=pensionista, gasto=None)

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

# ==================== CRUD COTIZACIONES ====================

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

# ==================== CRUD FINANZAS ====================

@app.route('/finanzas')
@login_required
def finanzas():
    # Leer filtros GET
    filtro_tipo = request.args.get('filtro_tipo', '')
    filtro_pagado = request.args.get('filtro_pagado', '')
    filtro_desde = request.args.get('filtro_desde', '')
    filtro_hasta = request.args.get('filtro_hasta', '')
    filtro_proveedor = request.args.get('filtro_proveedor', '')
    filtro_pensionista = request.args.get('filtro_pensionista', '')
    exportar = request.args.get('exportar', '')

    query = Finanzas.query

    # Filtros básicos
    if filtro_tipo in ['ingreso', 'egreso']:
        query = query.filter(Finanzas.tipo == filtro_tipo)
    if filtro_pagado == 'pagado':
        query = query.filter(Finanzas.pagado == True)
    elif filtro_pagado == 'pendiente':
        query = query.filter(Finanzas.pagado == False)
    # Filtro fecha desde/hasta
    if filtro_desde:
        query = query.filter(Finanzas.fecha >= filtro_desde)
    if filtro_hasta:
        query = query.filter(Finanzas.fecha <= filtro_hasta)
    # Filtro proveedor
    if filtro_proveedor:
        query = query.filter(Finanzas.proveedor.ilike(f"%{filtro_proveedor}%"))
    # Filtro pensionista
    if filtro_pensionista:
        query = query.filter(Finanzas.pensionista_id == int(filtro_pensionista))

    query = query.order_by(Finanzas.fecha.desc())
    finanzas = query.all()

    # Calcular totales según filtro
    total_ingresos = sum(f.monto for f in finanzas if f.tipo == 'ingreso')
    total_egresos = sum(f.monto for f in finanzas if f.tipo == 'egreso')
    saldo = total_ingresos - total_egresos

    # Exportar a Excel (solo lo filtrado)
    if exportar == 'excel':
        import pandas as pd
        data = []
        for f in finanzas:
            data.append({
                "Fecha": f.fecha.strftime('%d/%m/%Y') if f.fecha else '',
                "Tipo": f.tipo,
                "Concepto": f.concepto,
                "Monto": f.monto,
                "Pensionista": f.pensionista.nombre if f.pensionista else '',
                "Proveedor": f.proveedor or '',
                "Forma de Pago": f.forma_pago,
                "Pagado": 'Sí' if f.pagado else 'No',
            })
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="finanzas_filtrado.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # Para el filtro de pensionistas (selector)
    pensionistas_lista = Pensionista.query.order_by(Pensionista.nombre).all()

    return render_template(
        'finanzas.html',
        finanzas=finanzas,
        total_ingresos=total_ingresos,
        total_egresos=total_egresos,
        saldo=saldo,
        pensionistas_lista=pensionistas_lista
    )


@app.route('/finanzas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_finanza():
    pensionistas = Pensionista.query.all()
    clientes = Cliente.query.all()
    if request.method == 'POST':
        tipo = request.form['tipo']
        concepto = request.form['concepto']
        monto = float(request.form['monto'])
        fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d')
        pensionista_id = request.form.get('pensionista_id')
        pensionista_id = int(pensionista_id) if pensionista_id else None

        forma_pago = request.form['forma_pago']
        proveedor = request.form['proveedor'] if (tipo == 'egreso' and forma_pago == 'credito') else None

        # Lógica: Ingreso puede llevar cliente_id
        cliente_id = request.form.get('cliente_id') if tipo == 'ingreso' else None
        cliente_id = int(cliente_id) if cliente_id else None

        # Lógica pagado
        if tipo == "egreso" and forma_pago == "contado":
            pagado = True
        elif tipo == "egreso" and forma_pago == "credito":
            pagado = 'pagado' in request.form
        else:
            pagado = 'pagado' in request.form

        nueva = Finanzas(
            tipo=tipo,
            concepto=concepto,
            monto=monto,
            fecha=fecha,
            pensionista_id=pensionista_id,
            forma_pago=forma_pago,
            pagado=pagado,
            proveedor=proveedor,
            cliente_id=cliente_id
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Transacción financiera agregada correctamente', 'success')
        return redirect(url_for('finanzas'))
    return render_template('finanzas_form.html', finanza=None, pensionistas=pensionistas, clientes=clientes)

@app.route('/finanzas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_finanza(id):
    finanza = Finanzas.query.get_or_404(id)
    pensionistas = Pensionista.query.all()
    clientes = Cliente.query.all()
    if request.method == 'POST':
        finanza.tipo = request.form['tipo']
        finanza.concepto = request.form['concepto']
        finanza.monto = float(request.form['monto'])
        finanza.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d')
        pensionista_id = request.form.get('pensionista_id')
        finanza.pensionista_id = int(pensionista_id) if pensionista_id else None

        finanza.forma_pago = request.form['forma_pago']
        finanza.proveedor = request.form['proveedor'] if (finanza.tipo == 'egreso' and finanza.forma_pago == 'credito') else None

        # Lógica para editar el cliente asociado solo en ingresos
        finanza.cliente_id = int(request.form.get('cliente_id')) if finanza.tipo == 'ingreso' and request.form.get('cliente_id') else None

        if finanza.tipo == "egreso" and finanza.forma_pago == "contado":
            finanza.pagado = True
        elif finanza.tipo == "egreso" and finanza.forma_pago == "credito":
            finanza.pagado = 'pagado' in request.form
        else:
            finanza.pagado = 'pagado' in request.form

        db.session.commit()
        flash('Transacción financiera actualizada correctamente', 'success')
        return redirect(url_for('finanzas'))
    return render_template('finanzas_form.html', finanza=finanza, pensionistas=pensionistas, clientes=clientes)

@app.route('/finanzas/borrar/<int:id>')
@login_required
def finanza_borrar(id):
    finanza = Finanzas.query.get_or_404(id)
    db.session.delete(finanza)
    db.session.commit()
    flash('Movimiento financiero eliminado.', 'info')
    return redirect(url_for('finanzas'))

# ==================== INICIALIZACIÓN BASE Y USUARIOS DEMO ====================

if __name__ == '__main__':
    print("Rutas disponibles:")
    for rule in app.url_map.iter_rules():
        print(rule)
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='admin123', role='admin')
            db.session.add(admin)
            db.session.commit()
        if not User.query.filter_by(username='operador').first():
            operador = User(username='operador', password='operador123', role='operador')
            db.session.add(operador)
            db.session.commit()
    app.run(debug=True)
