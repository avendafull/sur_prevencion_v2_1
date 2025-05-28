from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import os

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta_segura'

# Crea la ruta absoluta a la base de datos en la carpeta instance
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'surprevencion.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MODELOS
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    nombre = db.Column(db.String(150))
    telefono = db.Column(db.String(50))
    password = db.Column(db.String(200))

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200))
    rut = db.Column(db.String(50), unique=True)
    contacto = db.Column(db.String(100))
    direccion = db.Column(db.String(200))
    cotizaciones = db.relationship('Cotizacion', backref='cliente', lazy=True)

class Cotizacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(50), unique=True)
    fecha = db.Column(db.Date)
    estado = db.Column(db.String(30))
    observaciones = db.Column(db.String(400))
    subtotal = db.Column(db.Float)
    iva = db.Column(db.Float)
    total = db.Column(db.Float)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    items = db.relationship('ItemCotizacion', backref='cotizacion', lazy=True)

class ItemCotizacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200))
    cantidad = db.Column(db.Integer)
    precio_unitario = db.Column(db.Float)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey('cotizacion.id'))

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date)
    tipo = db.Column(db.String(50))
    descripcion = db.Column(db.String(200))
    monto = db.Column(db.Float)

# LOGIN
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# RUTAS PRINCIPALES
@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', usuario=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        current_user.nombre = request.form['nombre']
        current_user.telefono = request.form['telefono']
        db.session.commit()
        flash('Datos actualizados')
    return render_template('perfil.html', usuario=current_user)

@app.route('/cambiar_contrasena', methods=['POST'])
@login_required
def cambiar_contrasena():
    actual = request.form['actual']
    nueva = request.form['nueva']
    repetir = request.form['repetir']
    if not check_password_hash(current_user.password, actual):
        flash('Contraseña actual incorrecta')
    elif nueva != repetir:
        flash('Las contraseñas no coinciden')
    else:
        current_user.password = generate_password_hash(nueva)
        db.session.commit()
        flash('Contraseña cambiada correctamente')
    return redirect(url_for('perfil'))

# CLIENTES
@app.route('/clientes')
@login_required
def clientes():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/agregar_cliente', methods=['GET', 'POST'])
@login_required
def agregar_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        rut = request.form['rut']
        contacto = request.form['contacto']
        direccion = request.form['direccion']
        if Cliente.query.filter_by(rut=rut).first():
            flash('Ya existe un cliente con ese RUT')
        else:
            cliente = Cliente(nombre=nombre, rut=rut, contacto=contacto, direccion=direccion)
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente agregado')
            return redirect(url_for('clientes'))
    return render_template('agregar_cliente.html')

# COTIZACIONES
@app.route('/cotizaciones')
@login_required
def cotizaciones():
    cotizaciones = Cotizacion.query.order_by(Cotizacion.fecha.desc()).all()
    return render_template('cotizaciones.html', cotizaciones=cotizaciones)

@app.route('/agregar_cotizacion', methods=['GET', 'POST'])
@login_required
def agregar_cotizacion():
    clientes = Cliente.query.all()
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d')
        observaciones = request.form['observaciones']
        estado = 'Pendiente'
        items = []
        subtotal = 0
        for i in range(1, 6):
            descripcion = request.form.get(f'descripcion_{i}')
            cantidad = request.form.get(f'cantidad_{i}')
            precio = request.form.get(f'precio_{i}')
            if descripcion and cantidad and precio:
                cantidad = int(cantidad)
                precio = float(precio)
                subtotal += cantidad * precio
                items.append({'descripcion': descripcion, 'cantidad': cantidad, 'precio_unitario': precio})
        iva = subtotal * 0.19
        total = subtotal + iva
        folio = f"COT-{int(datetime.now().timestamp())}"
        cotizacion = Cotizacion(
            folio=folio, fecha=fecha, estado=estado,
            observaciones=observaciones, subtotal=subtotal,
            iva=iva, total=total, cliente_id=cliente_id
        )
        db.session.add(cotizacion)
        db.session.commit()
        for item in items:
            db.session.add(ItemCotizacion(
                descripcion=item['descripcion'],
                cantidad=item['cantidad'],
                precio_unitario=item['precio_unitario'],
                cotizacion_id=cotizacion.id
            ))
        db.session.commit()
        flash('Cotización agregada')
        return redirect(url_for('cotizaciones'))
    return render_template('agregar_cotizacion.html', clientes=clientes)

# FINANZAS
@app.route('/finanzas')
@login_required
def finanzas():
    movimientos = Movimiento.query.order_by(Movimiento.fecha.desc()).all()
    ingresos = sum([m.monto for m in movimientos if m.tipo == 'Ingreso'])
    gastos = sum([m.monto for m in movimientos if m.tipo == 'Gasto'])
    balance = ingresos - gastos
    return render_template('finanzas.html', movimientos=movimientos, ingresos=ingresos, gastos=gastos, balance=balance)

@app.route('/agregar_movimiento', methods=['GET', 'POST'])
@login_required
def agregar_movimiento():
    if request.method == 'POST':
        fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d')
        tipo = request.form['tipo']
        descripcion = request.form['descripcion']
        monto = float(request.form['monto'])
        movimiento = Movimiento(fecha=fecha, tipo=tipo, descripcion=descripcion, monto=monto)
        db.session.add(movimiento)
        db.session.commit()
        flash('Movimiento registrado')
        return redirect(url_for('finanzas'))
    return render_template('agregar_movimiento.html')

# EXPORTACIÓN EXCEL
@app.route('/exportar_excel')
@login_required
def exportar_excel():
    movimientos = Movimiento.query.all()
    data = [{
        'Fecha': m.fecha.strftime('%Y-%m-%d'),
        'Tipo': m.tipo,
        'Descripción': m.descripcion,
        'Monto': m.monto
    } for m in movimientos]
    df = pd.DataFrame(data)
    file_path = 'movimientos.xlsx'
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

# --- INICIALIZACIÓN MANUAL DE BD Y ADMIN ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@surprevencion.cl').first():
        admin = User(
            email='admin@surprevencion.cl',
            nombre='Administrador',
            telefono='',
            password=generate_password_hash('1234')
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
