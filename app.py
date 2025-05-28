import datetime

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_segura_v3'
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'surprevencion.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
# Crear las tablas si no existen
with app.app_context():
    db.create_all()

login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    nombre = db.Column(db.String(150))
    telefono = db.Column(db.String(50))
    password = db.Column(db.String(200))

class TrabajadorHospedado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    empresa = db.Column(db.String(100))
    fecha_ingreso = db.Column(db.String(50))
    fecha_salida = db.Column(db.String(50))
    habitacion = db.Column(db.String(50))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

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
            flash('Correo o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/hospedaje', methods=['GET', 'POST'])
@login_required
def hospedaje():
    if request.method == 'POST':
        nombre = request.form['nombre']
        empresa = request.form['empresa']
        fecha_ingreso = request.form['fecha_ingreso']
        fecha_salida = request.form['fecha_salida']
        habitacion = request.form['habitacion']
        nuevo_trabajador = TrabajadorHospedado(
            nombre=nombre,
            empresa=empresa,
            fecha_ingreso=fecha_ingreso,
            fecha_salida=fecha_salida,
            habitacion=habitacion
        )
        db.session.add(nuevo_trabajador)
        db.session.commit()
        flash('Trabajador hospedado registrado correctamente.')
    trabajadores = TrabajadorHospedado.query.all()
    return render_template('hospedaje.html', trabajadores=trabajadores)

@app.route('/cotizaciones')
@login_required
def cotizaciones():
    return render_template('cotizaciones.html')

@app.route('/agregar_cliente')
@login_required
def agregar_cliente():
    return render_template('agregar_cliente.html')

@app.route('/agregar_cotizacion')
@login_required
def agregar_cotizacion():
    return render_template('agregar_cotizacion.html')

@app.route('/agregar_movimiento')
@login_required
def agregar_movimiento():
    return render_template('agregar_movimiento.html')

@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')


@app.route('/clientes')
@login_required
def clientes():
    # Datos simulados por ahora
    clientes = [
        {'nombre': 'Empresa A', 'rut': '12.345.678-9', 'contacto': 'Juan Pérez', 'direccion': 'Calle Falsa 123'},
        {'nombre': 'Empresa B', 'rut': '98.765.432-1', 'contacto': 'Ana Gómez', 'direccion': 'Avenida Siempre Viva 742'}
    ]
    return render_template('clientes.html', clientes=clientes)

@app.route('/finanzas')
@login_required
def finanzas():
    # Datos simulados por ahora
    movimientos = [
        {'fecha': datetime.datetime.now(), 'tipo': 'Ingreso', 'descripcion': 'Pago cliente', 'monto': 500000},
        {'fecha': datetime.datetime.now(), 'tipo': 'Gasto', 'descripcion': 'Compra insumos', 'monto': 150000}
    ]
    ingresos = sum(m['monto'] for m in movimientos if m['tipo'] == 'Ingreso')
    gastos = sum(m['monto'] for m in movimientos if m['tipo'] == 'Gasto')
    balance = ingresos - gastos
    return render_template('finanzas.html', movimientos=movimientos, ingresos=ingresos, gastos=gastos, balance=balance)

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        current_user.nombre = request.form['nombre']
        current_user.telefono = request.form['telefono']
        db.session.commit()
        flash('Perfil actualizado correctamente.')
    return render_template('perfil.html', usuario=current_user)

@app.route('/cambiar_contrasena', methods=['POST'])
@login_required
def cambiar_contrasena():
    actual = request.form['actual']
    nueva = request.form['nueva']
    repetir = request.form['repetir']
    if not check_password_hash(current_user.password, actual):
        flash('La contraseña actual no es correcta.')
    elif nueva != repetir:
        flash('Las nuevas contraseñas no coinciden.')
    else:
        current_user.password = generate_password_hash(nueva)
        db.session.commit()
        flash('Contraseña cambiada exitosamente.')
    return redirect(url_for('perfil'))


if __name__ == '__main__':
    app.run(debug=True)
