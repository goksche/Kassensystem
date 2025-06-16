from flask import Flask
from .database import db


def create_app():
    app = Flask(__name__)

    # Konfiguration laden (aus config.py im Projektverzeichnis)
    app.config.from_object("config")

    # Datenbank initialisieren
    db.init_app(app)

    with app.app_context():
        # Importiere Modelle und Routen
        from . import models
        from . import routes

        # Erstelle alle Tabellen in der Datenbank, falls nicht vorhanden
        db.create_all()

    return app
