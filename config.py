import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask-Konfiguration
# SECRET_KEY kann per Umgebungsvariable gesetzt werden
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance/kassensystem.sqlite')}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
