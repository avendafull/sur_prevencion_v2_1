
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from models import db, TrabajadorHospedado

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mikeyclave'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/surprevencion.db'
app.config['UPLOAD_FOLDER'] = 'instance'

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

from werkzeug.security import check_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('hospedaje'))
        else:
            flash('Usuario o contraseña inválido')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/hospedaje', methods=['GET', 'POST'])
@login_required
def hospedaje():
    if request.method == 'POST':
        nombre = request.form['nombre']
        fecha_llegada = datetime.strptime(request.form['fecha_llegada'], '%Y-%m-%d').date()
        fecha_salida = datetime.strptime(request.form['fecha_salida'], '%Y-%m-%d').date()
        valor_diario = float(request.form['valor_diario'])
        con_iva = 'con_iva' in request.form

        dias = (fecha_salida - fecha_llegada).days
        subtotal = valor_diario * dias
        total = subtotal * 1.19 if con_iva else subtotal

        archivo = request.files['archivo']
        filename = None
        if archivo and archivo.filename != '':
            filename = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        nuevo = TrabajadorHospedado(
            nombre=nombre,
            fecha_llegada=fecha_llegada,
            fecha_salida=fecha_salida,
            valor_diario=valor_diario,
            con_iva=con_iva,
            total=total,
            archivo=filename
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Registro guardado correctamente.')
        return redirect(url_for('hospedaje'))

    return render_template('hospedaje/hospedaje.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
