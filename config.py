import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-cambia-esto'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///surpensionistas.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
