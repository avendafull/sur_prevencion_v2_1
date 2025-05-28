
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_super_segura_para_produccion'

# Configuración base de datos
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

# Crear tablas si no existen
with app.app_context():
    db.create_all()

# Ruta básica para pruebas
@app.route('/')
def index():
    return render_template('index.html')  # Asegúrate de tener index.html

# Puedes ir agregando más rutas aquí como login, logout, dashboard, etc.

if __name__ == '__main__':
    app.run(debug=True)
