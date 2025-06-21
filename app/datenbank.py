from app import create_app
from app.database import db
import app.models  # wichtig, damit alle Tabellen geladen werden

if __name__ == "__main__":
    print("⚠️  Achtung: bestehende Datenbank wird gelöscht und neu erstellt.")
    confirm = input("Fortfahren? (ja/nein): ").strip().lower()
    if confirm == "ja":
        app = create_app()
        with app.app_context():
            db.drop_all()
            db.create_all()
            print("✅ Datenbank erfolgreich neu erstellt.")
    else:
        print("❌ Abgebrochen.")
