from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, instance_relative_config=True)

# Asegura que la carpeta 'instance' exista
os.makedirs(app.instance_path, exist_ok=True)

# Configura la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'surprevencion.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelos
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50))
    monto = db.Column(db.Float)
    descripcion = db.Column(db.String(200))

# Crear tablas y usuario admin si no existen
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin@surprevencion.cl').first():
        admin = User(username='admin@surprevencion.cl', password='1234')
        db.session.add(admin)
        db.session.commit()

# Rutas
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            return redirect(url_for('perfil'))
        else:
            return 'Usuario o contraseña incorrectos', 401
    return render_template('login.html')

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/finanzas')
def finanzas():
    movimientos = Movimiento.query.all()
    return render_template('finanzas.html', movimientos=movimientos)

@app.route('/agregar_movimiento', methods=['GET', 'POST'])
def agregar_movimiento():
    if request.method == 'POST':
        tipo = request.form['tipo']
        monto = float(request.form['monto'])
        descripcion = request.form['descripcion']
        nuevo_mov = Movimiento(tipo=tipo, monto=monto, descripcion=descripcion)
        db.session.add(nuevo_mov)
        db.session.commit()
        return redirect(url_for('finanzas'))
    return render_template('agregar_movimiento.html')

if __name__ == '__main__':
    app.run(debug=True)
