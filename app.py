from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/surprevencion.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Crear tablas si no existen
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin@surprevencion.cl').first():
        admin = User(username='admin@surprevencion.cl', password='1234')
        db.session.add(admin)
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
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
