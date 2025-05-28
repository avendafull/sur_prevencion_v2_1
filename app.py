from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuración de la base de datos SQLite en la carpeta instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/surprevencion.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# Crear tablas y usuario admin si no existe
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin@surprevencion.cl').first():
        admin_user = User(username='admin@surprevencion.cl', password='1234')
        db.session.add(admin_user)
        db.session.commit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Credenciales inválidas')
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
