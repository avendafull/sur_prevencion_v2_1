from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ==================== MODELO USUARIO ====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)

# ==================== MODELO CLIENTE ====================
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    rut = db.Column(db.String(20))
    contacto = db.Column(db.String(120))
    direccion = db.Column(db.String(250))

    cotizaciones = db.relationship('Cotizacion', backref='cliente', lazy=True)

# ==================== MODELO COTIZACIÓN ====================
class Cotizacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(20))
    monto = db.Column(db.Float)
    estado = db.Column(db.String(50))
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)

# ==================== MODELO PENSIONISTA ====================
class Pensionista(db.Model):
    __tablename__ = 'pensionista'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    empresa = db.Column(db.String(120))
    habitacion = db.Column(db.String(20))
    fecha_ingreso = db.Column(db.Date)
    monto_mensual = db.Column(db.Float, nullable=False)
    costo_alimentacion = db.Column(db.Float, nullable=False)  # NUEVO CAMPO

    gastos_extra = db.relationship('GastoExtra', backref='pensionista', lazy=True, cascade='all, delete-orphan')
    finanzas = db.relationship('Finanzas', backref='pensionista', lazy=True)

# ==================== MODELO GASTO EXTRA ====================
class GastoExtra(db.Model):
    __tablename__ = 'gasto_extra'
    id = db.Column(db.Integer, primary_key=True)
    pensionista_id = db.Column(db.Integer, db.ForeignKey('pensionista.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Float, nullable=False)

# ==================== MODELO FINANZAS ====================
class Finanzas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)        # 'ingreso' o 'egreso'
    concepto = db.Column(db.String(255), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    pensionista_id = db.Column(db.Integer, db.ForeignKey('pensionista.id'), nullable=True)
    proveedor = db.Column(db.String(100))                  # Proveedor para egresos
    forma_pago = db.Column(db.String(20))                  # 'contado' o 'credito'
    pagado = db.Column(db.Boolean, default=False)          # Estado de pago

    # Nuevo campo:
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)

    # Relación inversa
    cliente = db.relationship('Cliente', backref='finanzas', lazy=True)


# ==================== FIN DEL ARCHIVO ====================
