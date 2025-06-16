import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask-Konfiguration
SECRET_KEY = "super-secret-key"
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance/kassensystem.sqlite')}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
