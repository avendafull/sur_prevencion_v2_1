
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
