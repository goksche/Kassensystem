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
    bezahlt_status = db.Column(
        db.String(20),
        default="offen",
        nullable=False
    )

    teilnehmer = db.relationship("Teilnehmer", backref="events")


class Getraenk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    preis = db.Column(db.Float, nullable=False)
    kategorie = db.Column(db.String(50))

class Verkauf(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teilnehmer_event_id = db.Column(db.Integer, db.ForeignKey('teilnehmer_event.id'), nullable=False)
    getraenk_id = db.Column(db.Integer, db.ForeignKey('getraenk.id'), nullable=False)
    zeitpunkt = db.Column(db.DateTime, server_default=db.func.current_timestamp())

class Ausgabe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    betrag = db.Column(db.Float, nullable=False)
    kategorie = db.Column(db.String(50))
    beschreibung = db.Column(db.String(200))
    datum = db.Column(db.Date, nullable=False)

class Einnahme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    betrag = db.Column(db.Float, nullable=False)
    zahlungsmethode = db.Column(db.String(50))
    kommentar = db.Column(db.String(200))
    datum = db.Column(db.Date, nullable=False)
