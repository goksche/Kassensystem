from flask import render_template, request, redirect, url_for, Response
from flask import current_app as app
from .models import Event, Teilnehmer, TeilnehmerEvent, Getraenk, Verkauf
from .database import db
from datetime import datetime
from sqlalchemy import func
import csv
import io

@app.route("/")
def index():
    events = Event.query.order_by(Event.datum.desc()).all()
    teilnehmer = Teilnehmer.query.order_by(Teilnehmer.name).all()
    getraenke = Getraenk.query.order_by(Getraenk.kategorie).all()
    return render_template("index.html", events=events, teilnehmer=teilnehmer, getraenke=getraenke)

@app.route("/event", methods=["GET", "POST"])
def create_event():
    if request.method == "POST":
        name = request.form["name"]
        datum = datetime.strptime(request.form["datum"], "%Y-%m-%d").date()
        neues_event = Event(name=name, datum=datum)
        db.session.add(neues_event)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("event_form.html")

@app.route("/event/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == "POST":
        event.name = request.form["name"]
        event.datum = datetime.strptime(request.form["datum"], "%Y-%m-%d").date()
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("event_edit.html", event=event)
@app.route("/teilnehmer", methods=["GET", "POST"])
def create_teilnehmer():
    events = Event.query.order_by(Event.datum.desc()).all()
    if request.method == "POST":
        name = request.form["name"]
        event_id = request.form["event_id"]
        teilnehmer = Teilnehmer(name=name)
        db.session.add(teilnehmer)
        db.session.commit()
        teilnehmer_event = TeilnehmerEvent(teilnehmer_id=teilnehmer.id, event_id=event_id, bezahlt_status="offen")
        db.session.add(teilnehmer_event)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("teilnehmer_form.html", events=events)
@app.route("/teilnehmer/edit/<int:teilnehmer_id>", methods=["GET", "POST"])
def edit_teilnehmer(teilnehmer_id):
    teilnehmer = Teilnehmer.query.get_or_404(teilnehmer_id)

    if request.method == "POST":
        teilnehmer.name = request.form["name"]
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("teilnehmer_edit.html", teilnehmer=teilnehmer)
@app.route("/getraenk", methods=["GET", "POST"])
def create_getraenk():
    if request.method == "POST":
        name = request.form["name"]
        preis = float(request.form["preis"])
        kategorie = request.form["kategorie"]
        getraenk = Getraenk(name=name, preis=preis, kategorie=kategorie)
        db.session.add(getraenk)
        db.session.commit()
        return redirect(url_for("list_getraenke"))
    return render_template("getraenk_form.html")

@app.route("/getraenke")
def list_getraenke():
    getraenke = Getraenk.query.order_by(Getraenk.kategorie).all()
    return render_template("getraenk_liste.html", getraenke=getraenke)
@app.route("/verkauf", methods=["GET", "POST"])
def erfasse_verkauf():
    events = Event.query.order_by(Event.datum.desc()).all()
    if request.method == "POST":
        event_id = int(request.form["event_id"])
        teilnehmer_event_id = int(request.form["teilnehmer_event_id"])
        getraenk_id = int(request.form["getraenk_id"])
        verkauf = Verkauf(teilnehmer_event_id=teilnehmer_event_id, getraenk_id=getraenk_id)
        db.session.add(verkauf)
        db.session.commit()
        return redirect(url_for("index"))

    selected_event_id = request.args.get("event_id", type=int)
    teilnehmer_event_liste = []
    if selected_event_id:
        teilnehmer_event_liste = TeilnehmerEvent.query.filter_by(event_id=selected_event_id).all()
    getraenke = Getraenk.query.all()
    return render_template("verkauf_form.html", events=events, teilnehmer_events=teilnehmer_event_liste, getraenke=getraenke, selected_event_id=selected_event_id)

@app.route("/uebersicht")
def event_uebersicht():
    event_id = request.args.get("event_id", type=int)
    events = Event.query.order_by(Event.datum.desc()).all()
    data = []

    if event_id:
        teilnehmer_events = TeilnehmerEvent.query.filter_by(event_id=event_id).all()
        for te in teilnehmer_events:
            name = te.teilnehmer.name
            buchungen = (
                db.session.query(Getraenk.name, func.count(Verkauf.id), func.sum(Getraenk.preis))
                .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
                .filter(Verkauf.teilnehmer_event_id == te.id)
                .group_by(Getraenk.name)
                .all()
            )
            data.append({
                "teilnehmer": name,
                "buchungen": buchungen,
                "gesamt": sum(row[2] or 0 for row in buchungen),
                "status": te.bezahlt_status
            })

    return render_template("event_uebersicht.html", events=events, selected_event_id=event_id, daten=data)
@app.route("/uebersicht/export_csv")
def export_csv():
    event_id = request.args.get("event_id", type=int)
    if not event_id:
        return redirect(url_for("event_uebersicht"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Teilnehmer", "Getränk", "Menge", "Betrag", "Status"])

    teilnehmer_events = TeilnehmerEvent.query.filter_by(event_id=event_id).all()
    for te in teilnehmer_events:
        buchungen = (
            db.session.query(Getraenk.name, func.count(Verkauf.id), func.sum(Getraenk.preis))
            .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
            .filter(Verkauf.teilnehmer_event_id == te.id)
            .group_by(Getraenk.name)
            .all()
        )
        for eintrag in buchungen:
            writer.writerow([
                te.teilnehmer.name,
                eintrag[0],
                eintrag[1],
                f"{eintrag[2]:.2f}",
                te.bezahlt_status
            ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=event_{event_id}_teilnehmer.csv"}
    )

@app.route("/export/umsatz")
def export_umsatz():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Event", "Getränk", "Menge", "Umsatz CHF"])

    events = Event.query.order_by(Event.datum).all()
    gesamtumsatz = 0.0

    for event in events:
        verkaufsdaten = (
            db.session.query(Getraenk.name, func.count(Verkauf.id), func.sum(Getraenk.preis))
            .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
            .join(TeilnehmerEvent, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .filter(TeilnehmerEvent.event_id == event.id)
            .group_by(Getraenk.name)
            .all()
        )
        for row in verkaufsdaten:
            writer.writerow([event.name, row[0], row[1], f"{row[2]:.2f}"])
            gesamtumsatz += row[2] or 0

    writer.writerow([])
    writer.writerow(["GESAMT", "", "", f"{gesamtumsatz:.2f}"])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=umsatzuebersicht.csv"}
    )
@app.route("/zahlung", methods=["GET", "POST"])
def zahlung_verwalten():
    events = Event.query.order_by(Event.datum.desc()).all()
    selected_event_id = request.args.get("event_id", type=int)
    teilnehmer_events = []

    if selected_event_id:
        teilnehmer_events = TeilnehmerEvent.query.filter_by(event_id=selected_event_id).all()

    if request.method == "POST":
        for te in teilnehmer_events:
            status = request.form.get(f"status_{te.id}")
            te.bezahlt_status = status
        db.session.commit()
        return redirect(url_for("zahlung_verwalten", event_id=selected_event_id))

    return render_template("zahlung_verwalten.html", events=events, teilnehmer_events=teilnehmer_events, selected_event_id=selected_event_id)

@app.route("/teilnehmerreport")
def teilnehmer_report():
    teilnehmer_liste = Teilnehmer.query.order_by(Teilnehmer.name).all()
    daten = []

    for t in teilnehmer_liste:
        teilnahmen = (
            db.session.query(Event.name, func.count(Verkauf.id), func.sum(Getraenk.preis))
            .join(TeilnehmerEvent, TeilnehmerEvent.event_id == Event.id)
            .join(Verkauf, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .join(Getraenk, Getraenk.id == Verkauf.getraenk_id)
            .filter(TeilnehmerEvent.teilnehmer_id == t.id)
            .group_by(Event.name)
            .all()
        )
        gesamt = sum(row[2] or 0 for row in teilnahmen)
        daten.append({
            "teilnehmer": t.name,
            "events": teilnahmen,
            "gesamt": gesamt
        })

    return render_template("teilnehmer_report.html", daten=daten)

@app.route("/teilnehmerreport/export_csv")
def teilnehmer_report_export():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Teilnehmer", "Event", "Anzahl Getränke", "Gesamt CHF"])

    teilnehmer_liste = Teilnehmer.query.order_by(Teilnehmer.name).all()
    for t in teilnehmer_liste:
        teilnahmen = (
            db.session.query(Event.name, func.count(Verkauf.id), func.sum(Getraenk.preis))
            .join(TeilnehmerEvent, TeilnehmerEvent.event_id == Event.id)
            .join(Verkauf, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .join(Getraenk, Getraenk.id == Verkauf.getraenk_id)
            .filter(TeilnehmerEvent.teilnehmer_id == t.id)
            .group_by(Event.name)
            .all()
        )
        for row in teilnahmen:
            writer.writerow([t.name, row[0], row[1], f"{row[2]:.2f}"])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=teilnehmer_report.csv"}
    )
@app.route("/getraenk/edit/<int:getraenk_id>", methods=["GET", "POST"])
def edit_getraenk(getraenk_id):
    getraenk = Getraenk.query.get_or_404(getraenk_id)

    if request.method == "POST":
        getraenk.name = request.form["name"]
        getraenk.preis = float(request.form["preis"])
        getraenk.kategorie = request.form["kategorie"]
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("getraenk_edit.html", getraenk=getraenk)