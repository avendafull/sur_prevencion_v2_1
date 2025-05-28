
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_super_segura_para_produccion'
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'surprevencion.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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
    descripcion = db.Column(db.String(300))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    monto = db.Column(db.Float)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)

class TrabajadorHospedado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    fecha_llegada = db.Column(db.Date, nullable=False)
    fecha_salida = db.Column(db.Date, nullable=False)
    valor_diario = db.Column(db.Float, nullable=False)
    con_iva = db.Column(db.Boolean, default=False)
    total = db.Column(db.Float)
    archivo = db.Column(db.String(200))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

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
            flash('Credenciales incorrectas')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/clientes')
@login_required
def clientes():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/agregar_cliente', methods=['GET', 'POST'])
@login_required
def agregar_cliente():
    if request.method == 'POST':
        nuevo = Cliente(
            nombre=request.form['nombre'],
            rut=request.form['rut'],
            contacto=request.form['contacto'],
            direccion=request.form['direccion']
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('clientes'))
    return render_template('agregar_cliente.html')

@app.route('/cotizaciones')
@login_required
def cotizaciones():
    cotizaciones = Cotizacion.query.all()
    return render_template('cotizaciones.html', cotizaciones=cotizaciones)

@app.route('/agregar_cotizacion', methods=['GET', 'POST'])
@login_required
def agregar_cotizacion():
    clientes = Cliente.query.all()
    if request.method == 'POST':
        nueva = Cotizacion(
            descripcion=request.form['descripcion'],
            monto=float(request.form['monto']),
            cliente_id=int(request.form['cliente_id'])
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect(url_for('cotizaciones'))
    return render_template('agregar_cotizacion.html', clientes=clientes)

@app.route('/hospedaje')
@login_required
def hospedaje():
    hospedados = TrabajadorHospedado.query.all()
    return render_template('hospedaje.html', hospedados=hospedados)

@app.route('/finanzas')
@login_required
def finanzas():
    return render_template('finanzas.html')

@app.route('/agregar_movimiento')
@login_required
def agregar_movimiento():
    return render_template('agregar_movimiento.html')

@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html', user=current_user)
