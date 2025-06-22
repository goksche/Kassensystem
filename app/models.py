from .database import db

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    datum = db.Column(db.Date, nullable=False)

class Teilnehmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class TeilnehmerEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    teilnehmer_id = db.Column(db.Integer, db.ForeignKey('teilnehmer.id'), nullable=False)
    bezahlt_status = db.Column(db.String(20), default="offen", nullable=False)

    event = db.relationship("Event", backref="teilnehmerzuordnung")
    teilnehmer = db.relationship("Teilnehmer", backref="events")

class Getraenk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    preis = db.Column(db.Float, nullable=False)
    kategorie = db.Column(db.String(50), nullable=False)

class Verkauf(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teilnehmer_event_id = db.Column(db.Integer, db.ForeignKey('teilnehmer_event.id'), nullable=False)
    getraenk_id = db.Column(db.Integer, db.ForeignKey('getraenk.id'), nullable=False)
    menge = db.Column(db.Integer, default=1)
    zeitpunkt = db.Column(db.DateTime, server_default=db.func.now())

    teilnehmer_event = db.relationship("TeilnehmerEvent", backref="verkaeufe")
    getraenk = db.relationship("Getraenk")

class Ausgabe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    kategorie = db.Column(db.String(50), nullable=False)
    beschreibung = db.Column(db.String(200), nullable=True)
    betrag = db.Column(db.Float, nullable=False)
    datum = db.Column(db.Date, nullable=False, default=db.func.current_date())

    event = db.relationship("Event", backref="ausgaben")

class Einnahme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    quelle = db.Column(db.String(50), nullable=False)
    betrag = db.Column(db.Float, nullable=False)

    event = db.relationship("Event", backref="einnahmen")
