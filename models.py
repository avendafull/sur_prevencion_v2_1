from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='operador')  # 'admin' o 'operador'

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    rut = db.Column(db.String(12))
    contacto = db.Column(db.String(100))
    direccion = db.Column(db.String(200))

class Cotizacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date)
    monto = db.Column(db.Float)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    cliente = db.relationship('Cliente', backref=db.backref('cotizaciones', lazy=True))
    estado = db.Column(db.String(50))


class Pensionista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    empresa = db.Column(db.String(100))
    habitacion = db.Column(db.String(50))
    fecha_ingreso = db.Column(db.Date)
    monto_mensual = db.Column(db.Float)  # <-- Cambiado a mensual
    gastos_extra = db.relationship('GastoExtra', backref='pensionista', lazy=True)
    # fecha_salida puede quedar nullable o eliminarse si no se usa

class GastoExtra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100))
    monto = db.Column(db.Float)
    fecha = db.Column(db.Date)
    pensionista_id = db.Column(db.Integer, db.ForeignKey('pensionista.id'))

class Finanzas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20))  # ingreso/egreso
    concepto = db.Column(db.String(100))
    monto = db.Column(db.Float)
    fecha = db.Column(db.Date)
    pensionista_id = db.Column(db.Integer, db.ForeignKey('pensionista.id'), nullable=True)
    recibido_de = db.Column(db.String(100))  # <<--- agrega esto
    estado_pago = db.Column(db.String(20), default="Pagado")  # "Pagado" o "Pendiente"
