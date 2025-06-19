from .models import Ausgabe
from flask import render_template, request, redirect, url_for, Response
from flask import current_app as app
from .models import Event, Teilnehmer, TeilnehmerEvent, Getraenk, Verkauf, Ausgabe, Einnahme
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
    return render_template(
        "index.html",
        events=events,
        teilnehmer=teilnehmer,
        getraenke=getraenke,
        now=datetime.now()  # ← NEU hinzugefügt
    )

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
@app.route("/teilnehmer/neu", methods=["GET", "POST"])
def create_teilnehmer():
    if request.method == "POST":
        name = request.form["name"]
        teilnehmer = Teilnehmer(name=name)
        db.session.add(teilnehmer)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("teilnehmer_create.html")

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
    teilnehmer = Teilnehmer.query.order_by(Teilnehmer.name).all()
    getraenke = Getraenk.query.order_by(Getraenk.kategorie).all()

    if request.method == "POST":
        event_id = request.form["event"]
        teilnehmer_id = request.form["teilnehmer"]
        getraenk_id = request.form["getraenk"]
        menge = int(request.form.get("menge", 1))

        teilnehmer_event = TeilnehmerEvent.query.filter_by(event_id=event_id, teilnehmer_id=teilnehmer_id).first()
        if not teilnehmer_event:
            teilnehmer_event = TeilnehmerEvent(event_id=event_id, teilnehmer_id=teilnehmer_id, bezahlt_status="offen")
            db.session.add(teilnehmer_event)
            db.session.commit()

        for _ in range(menge):
            verkauf = Verkauf(teilnehmer_event_id=teilnehmer_event.id, getraenk_id=getraenk_id)
            db.session.add(verkauf)

        db.session.commit()
        return redirect(url_for("index"))

    return render_template("verkauf.html", events=events, teilnehmer=teilnehmer, getraenke=getraenke)

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
@app.route("/event/<int:event_id>/teilnehmer", methods=["GET", "POST"])
def zuweise_teilnehmer(event_id):
    event = Event.query.get_or_404(event_id)
    alle_teilnehmer = Teilnehmer.query.order_by(Teilnehmer.name).all()

    if request.method == "POST":
        ausgewaehlt_ids = request.form.getlist("teilnehmer")
        for teilnehmer in alle_teilnehmer:
            zuweisung = TeilnehmerEvent.query.filter_by(event_id=event.id, teilnehmer_id=teilnehmer.id).first()

            if str(teilnehmer.id) in ausgewaehlt_ids and not zuweisung:
                neu = TeilnehmerEvent(event_id=event.id, teilnehmer_id=teilnehmer.id, bezahlt_status="offen")
                db.session.add(neu)
            elif str(teilnehmer.id) not in ausgewaehlt_ids and zuweisung:
                db.session.delete(zuweisung)

        db.session.commit()
        return redirect(url_for("index"))

    bestehende_ids = [te.teilnehmer_id for te in TeilnehmerEvent.query.filter_by(event_id=event.id).all()]
    return render_template("event_teilnehmer_zuweisung.html", event=event, teilnehmer=alle_teilnehmer, bestehende_ids=bestehende_ids)
@app.route("/auswertung/umsatz_jahr")
def umsatz_pro_jahr():
    daten = (
        db.session.query(func.strftime('%Y', Verkauf.zeitpunkt).label("jahr"), func.sum(Getraenk.preis))
        .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
        .group_by("jahr")
        .order_by("jahr")
        .all()
    )
    return render_template("umsatz_jahr.html", daten=daten)

@app.route("/auswertung/umsatz_jahr/export_csv")
def export_umsatz_pro_jahr_csv():
    daten = (
        db.session.query(func.strftime('%Y', Verkauf.zeitpunkt).label("jahr"), func.sum(Getraenk.preis))
        .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
        .group_by("jahr")
        .order_by("jahr")
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Jahr", "Umsatz CHF"])

    for row in daten:
        writer.writerow([row[0], f"{row[1]:.2f}"])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=umsatz_pro_jahr.csv"}
    )
@app.route("/auswertung/umsatz_teilnehmer")
def umsatz_pro_teilnehmer():
    daten = (
        db.session.query(Teilnehmer.name, func.sum(Getraenk.preis))
        .join(TeilnehmerEvent, Teilnehmer.id == TeilnehmerEvent.teilnehmer_id)
        .join(Verkauf, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
        .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
        .group_by(Teilnehmer.id)
        .order_by(func.sum(Getraenk.preis).desc())
        .all()
    )
    return render_template("umsatz_teilnehmer.html", daten=daten)

@app.route("/auswertung/umsatz_teilnehmer/export_csv")
def export_umsatz_pro_teilnehmer_csv():
    daten = (
        db.session.query(Teilnehmer.name, func.sum(Getraenk.preis))
        .join(TeilnehmerEvent, Teilnehmer.id == TeilnehmerEvent.teilnehmer_id)
        .join(Verkauf, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
        .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
        .group_by(Teilnehmer.id)
        .order_by(func.sum(Getraenk.preis).desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Teilnehmer", "Umsatz CHF"])

    for row in daten:
        writer.writerow([row[0], f"{row[1]:.2f}"])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=umsatz_pro_teilnehmer.csv"}
    )
@app.route("/auswertung/getraenkestatistik")
def getraenkestatistik():
    daten = (
        db.session.query(Getraenk.name, func.count(Verkauf.id), func.sum(Getraenk.preis))
        .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
        .group_by(Getraenk.id)
        .order_by(func.count(Verkauf.id).desc())
        .all()
    )
    return render_template("getraenkestatistik.html", daten=daten)

@app.route("/auswertung/getraenkestatistik/export_csv")
def export_getraenkestatistik_csv():
    daten = (
        db.session.query(Getraenk.name, func.count(Verkauf.id), func.sum(Getraenk.preis))
        .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
        .group_by(Getraenk.id)
        .order_by(func.count(Verkauf.id).desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Getränk", "Anzahl verkauft", "Umsatz CHF"])

    for row in daten:
        writer.writerow([row[0], row[1], f"{row[2]:.2f}"])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=getraenkestatistik.csv"}
    )
@app.route("/auswertung/verbrauch_pro_teilnehmer")
def verbrauch_pro_teilnehmer():
    teilnehmer_liste = Teilnehmer.query.order_by(Teilnehmer.name).all()
    daten = []

    for t in teilnehmer_liste:
        # Gesamtverbrauch
        gesamt = (
            db.session.query(func.sum(Getraenk.preis))
            .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
            .join(TeilnehmerEvent, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .filter(TeilnehmerEvent.teilnehmer_id == t.id)
            .scalar() or 0.0
        )

        # Jahresverbrauch
        jahre = (
            db.session.query(func.strftime('%Y', Verkauf.zeitpunkt), func.sum(Getraenk.preis))
            .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
            .join(TeilnehmerEvent, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .filter(TeilnehmerEvent.teilnehmer_id == t.id)
            .group_by(func.strftime('%Y', Verkauf.zeitpunkt))
            .order_by(func.strftime('%Y', Verkauf.zeitpunkt))
            .all()
        )

        # Eventverbrauch
        events = (
            db.session.query(Event.name, func.sum(Getraenk.preis))
            .join(TeilnehmerEvent, TeilnehmerEvent.event_id == Event.id)
            .join(Verkauf, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
            .filter(TeilnehmerEvent.teilnehmer_id == t.id)
            .group_by(Event.name)
            .order_by(Event.datum)
            .all()
        )

        daten.append({
            "teilnehmer": t.name,
            "gesamt": gesamt,
            "jahre": jahre,
            "events": events
        })

    return render_template("verbrauch_teilnehmer.html", daten=daten)
@app.route("/auswertung/teilnehmerliste")
def teilnehmerliste():
    daten = (
        db.session.query(Teilnehmer.name, func.count(TeilnehmerEvent.id))
        .outerjoin(TeilnehmerEvent, Teilnehmer.id == TeilnehmerEvent.teilnehmer_id)
        .group_by(Teilnehmer.id)
        .order_by(Teilnehmer.name)
        .all()
    )
    return render_template("teilnehmerliste.html", daten=daten)

@app.route("/auswertung/teilnehmerliste/export_csv")
def export_teilnehmerliste_csv():
    daten = (
        db.session.query(Teilnehmer.name, func.count(TeilnehmerEvent.id))
        .outerjoin(TeilnehmerEvent, Teilnehmer.id == TeilnehmerEvent.teilnehmer_id)
        .group_by(Teilnehmer.id)
        .order_by(Teilnehmer.name)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Teilnehmer", "Teilnahmen"])

    for row in daten:
        writer.writerow([row[0], row[1]])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=teilnehmerliste.csv"}
    )
@app.route("/auswertung/teilnehmerliste_event")
def teilnehmerliste_pro_event():
    events = Event.query.order_by(Event.datum.desc()).all()
    selected_event_id = request.args.get("event_id", type=int)
    daten = []

    if selected_event_id:
        daten = (
            db.session.query(Teilnehmer.name, TeilnehmerEvent.bezahlt_status)
            .join(Teilnehmer, Teilnehmer.id == TeilnehmerEvent.teilnehmer_id)
            .filter(TeilnehmerEvent.event_id == selected_event_id)
            .order_by(Teilnehmer.name)
            .all()
        )

    return render_template("teilnehmerliste_event.html", events=events, daten=daten, selected_event_id=selected_event_id)

@app.route("/auswertung/teilnehmerliste_event/export_csv")
def export_teilnehmerliste_event_csv():
    event_id = request.args.get("event_id", type=int)
    if not event_id:
        return redirect(url_for("teilnehmerliste_pro_event"))

    daten = (
        db.session.query(Teilnehmer.name, TeilnehmerEvent.bezahlt_status)
        .join(Teilnehmer, Teilnehmer.id == TeilnehmerEvent.teilnehmer_id)
        .filter(TeilnehmerEvent.event_id == event_id)
        .order_by(Teilnehmer.name)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Teilnehmer", "Bezahlstatus"])

    for row in daten:
        writer.writerow([row[0], row[1]])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=teilnehmer_event_{event_id}.csv"}
    )
@app.route("/auswertung/einzelabrechnung_event")
def einzelabrechnung_event():
    events = Event.query.order_by(Event.datum.desc()).all()
    selected_event_id = request.args.get("event_id", type=int)
    daten = []

    if selected_event_id:
        teilnehmer_events = TeilnehmerEvent.query.filter_by(event_id=selected_event_id).all()

        for te in teilnehmer_events:
            buchungen = (
                db.session.query(Getraenk.name, func.count(Verkauf.id), Getraenk.preis, func.sum(Getraenk.preis))
                .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
                .filter(Verkauf.teilnehmer_event_id == te.id)
                .group_by(Getraenk.name)
                .all()
            )

            gesamtbetrag = sum(row[3] or 0 for row in buchungen)

            daten.append({
                "teilnehmer": te.teilnehmer.name,
                "buchungen": buchungen,
                "gesamt": gesamtbetrag,
                "status": te.bezahlt_status
            })

    return render_template("einzelabrechnung_event.html", events=events, daten=daten, selected_event_id=selected_event_id)
@app.route("/auswertung/umsatzverlauf")
def umsatzverlauf():
    daten = (
        db.session.query(func.date(Verkauf.zeitpunkt), func.sum(Getraenk.preis))
        .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
        .group_by(func.date(Verkauf.zeitpunkt))
        .order_by(func.date(Verkauf.zeitpunkt))
        .all()
    )
    return render_template("umsatzverlauf.html", daten=daten)

@app.route("/auswertung/umsatzverlauf/export_csv")
def export_umsatzverlauf_csv():
    daten = (
        db.session.query(func.date(Verkauf.zeitpunkt), func.sum(Getraenk.preis))
        .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
        .group_by(func.date(Verkauf.zeitpunkt))
        .order_by(func.date(Verkauf.zeitpunkt))
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Datum", "Umsatz CHF"])

    for row in daten:
        writer.writerow([row[0], f"{row[1]:.2f}"])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=umsatzverlauf.csv"}
    )
from flask import make_response, render_template, request, redirect, url_for
import io
from xhtml2pdf import pisa

@app.route("/auswertung/einzelabrechnung_event/pdf")
def einzelabrechnung_event_pdf():
    event_id = request.args.get("event_id", type=int)
    if not event_id:
        return redirect(url_for("einzelabrechnung_event"))

    event = Event.query.get_or_404(event_id)
    teilnehmer_events = TeilnehmerEvent.query.filter_by(event_id=event.id).all()
    daten = []

    for te in teilnehmer_events:
        buchungen = (
            db.session.query(Getraenk.name, func.count(Verkauf.id), Getraenk.preis, func.sum(Getraenk.preis))
            .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
            .filter(Verkauf.teilnehmer_event_id == te.id)
            .group_by(Getraenk.name)
            .all()
        )

        gesamtbetrag = sum(row[3] or 0 for row in buchungen)

        daten.append({
            "teilnehmer": te.teilnehmer.name,
            "buchungen": buchungen,
            "gesamt": gesamtbetrag,
            "status": te.bezahlt_status
        })

    # Render HTML für PDF
    html = render_template("einzelabrechnung_pdf.html", event=event, daten=daten)

    # PDF in Memory-Puffer schreiben
    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    # Response mit PDF-Inhalt zurückgeben
    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=einzelabrechnung_event_{event.id}.pdf'
    return response
@app.route("/teilnehmerreport/pdf")
def teilnehmer_report_pdf():
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

    html = render_template("teilnehmerreport_pdf.html", daten=daten)

    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=teilnehmerreport.pdf'
    return response
@app.route("/export/umsatz/pdf")
def export_umsatz_pdf():
    events = Event.query.order_by(Event.datum).all()
    daten = []
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
        summe_event = sum(row[2] or 0 for row in verkaufsdaten)
        gesamtumsatz += summe_event

        daten.append({
            "event": event,
            "verkauf": verkaufsdaten,
            "summe": summe_event
        })

    html = render_template("umsatz_pro_event_pdf.html", daten=daten, gesamtumsatz=gesamtumsatz)

    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=umsatz_pro_event.pdf'
    return response
@app.route("/export/umsatz_jahr/pdf")
def export_umsatz_pro_jahr_pdf():
    daten = (
        db.session.query(func.strftime('%Y', Verkauf.zeitpunkt).label("jahr"), func.sum(Getraenk.preis))
        .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
        .group_by("jahr")
        .order_by("jahr")
        .all()
    )

    gesamtumsatz = sum(row[1] or 0 for row in daten)

    html = render_template("umsatz_pro_jahr_pdf.html", daten=daten, gesamtumsatz=gesamtumsatz)

    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=umsatz_pro_jahr.pdf'
    return response
@app.route("/export/umsatz_teilnehmer/pdf")
def export_umsatz_pro_teilnehmer_pdf():
    daten = (
        db.session.query(Teilnehmer.name, func.sum(Getraenk.preis))
        .join(TeilnehmerEvent, Teilnehmer.id == TeilnehmerEvent.teilnehmer_id)
        .join(Verkauf, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
        .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
        .group_by(Teilnehmer.id)
        .order_by(func.sum(Getraenk.preis).desc())
        .all()
    )

    gesamtumsatz = sum(row[1] or 0 for row in daten)

    html = render_template("umsatz_pro_teilnehmer_pdf.html", daten=daten, gesamtumsatz=gesamtumsatz)

    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=umsatz_pro_teilnehmer.pdf'
    return response
@app.route("/export/getraenkestatistik/pdf")
def export_getraenkestatistik_pdf():
    daten = (
        db.session.query(Getraenk.name, func.count(Verkauf.id), func.sum(Getraenk.preis))
        .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
        .group_by(Getraenk.id)
        .order_by(func.count(Verkauf.id).desc())
        .all()
    )

    gesamtumsatz = sum(row[2] or 0 for row in daten)

    html = render_template("getraenkestatistik_pdf.html", daten=daten, gesamtumsatz=gesamtumsatz)

    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=getraenkestatistik.pdf'
    return response
@app.route("/export/verbrauch_teilnehmer/pdf")
def export_verbrauch_pro_teilnehmer_pdf():
    teilnehmer_liste = Teilnehmer.query.order_by(Teilnehmer.name).all()
    daten = []

    for t in teilnehmer_liste:
        # Gesamtverbrauch
        gesamt = (
            db.session.query(func.sum(Getraenk.preis))
            .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
            .join(TeilnehmerEvent, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .filter(TeilnehmerEvent.teilnehmer_id == t.id)
            .scalar() or 0.0
        )

        # Jahresverbrauch
        jahre = (
            db.session.query(func.strftime('%Y', Verkauf.zeitpunkt), func.sum(Getraenk.preis))
            .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
            .join(TeilnehmerEvent, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .filter(TeilnehmerEvent.teilnehmer_id == t.id)
            .group_by(func.strftime('%Y', Verkauf.zeitpunkt))
            .order_by(func.strftime('%Y', Verkauf.zeitpunkt))
            .all()
        )

        # Eventverbrauch
        events = (
            db.session.query(Event.name, func.sum(Getraenk.preis))
            .join(TeilnehmerEvent, TeilnehmerEvent.event_id == Event.id)
            .join(Verkauf, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .join(Getraenk, Verkauf.getraenk_id == Getraenk.id)
            .filter(TeilnehmerEvent.teilnehmer_id == t.id)
            .group_by(Event.name)
            .order_by(Event.datum)
            .all()
        )

        daten.append({
            "teilnehmer": t.name,
            "gesamt": gesamt,
            "jahre": jahre,
            "events": events
        })

    html = render_template("verbrauch_pro_teilnehmer_pdf.html", daten=daten)

    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=verbrauch_pro_teilnehmer.pdf'
    return response
@app.route("/export/teilnehmerliste/pdf")
def export_teilnehmerliste_pdf():
    daten = (
        db.session.query(Teilnehmer.name, func.count(TeilnehmerEvent.id))
        .outerjoin(TeilnehmerEvent, Teilnehmer.id == TeilnehmerEvent.teilnehmer_id)
        .group_by(Teilnehmer.id)
        .order_by(Teilnehmer.name)
        .all()
    )

    html = render_template("teilnehmerliste_pdf.html", daten=daten)

    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=teilnehmerliste.pdf'
    return response
@app.route("/export/teilnehmerliste_event/pdf")
def export_teilnehmerliste_event_pdf():
    event_id = request.args.get("event_id", type=int)
    if not event_id:
        return redirect(url_for('teilnehmerliste_pro_event'))

    event = Event.query.get_or_404(event_id)
    daten = (
        db.session.query(Teilnehmer.name, TeilnehmerEvent.bezahlt_status)
        .join(Teilnehmer, Teilnehmer.id == TeilnehmerEvent.teilnehmer_id)
        .filter(TeilnehmerEvent.event_id == event_id)
        .order_by(Teilnehmer.name)
        .all()
    )

    html = render_template("teilnehmerliste_pro_event_pdf.html", event=event, daten=daten)

    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=teilnehmerliste_event_{event_id}.pdf'
    return response
@app.route("/ausgaben", methods=["GET", "POST"])
def erfasse_ausgabe():
    events = Event.query.order_by(Event.datum.desc()).all()

    if request.method == "POST":
        event_id = request.form["event_id"]
        betrag = float(request.form["betrag"])
        kategorie = request.form["kategorie"]
        beschreibung = request.form["beschreibung"]
        datum = datetime.strptime(request.form["datum"], "%Y-%m-%d").date()

        neue_ausgabe = Ausgabe(
            event_id=event_id,
            betrag=betrag,
            kategorie=kategorie,
            beschreibung=beschreibung,
            datum=datum
        )
        db.session.add(neue_ausgabe)
        db.session.commit()
        return redirect(url_for("erfasse_ausgabe"))

    ausgaben = (
        db.session.query(Ausgabe, Event.name)
        .join(Event, Ausgabe.event_id == Event.id)
        .order_by(Ausgabe.datum.desc())
        .all()
    )

    return render_template("ausgabe_form.html", events=events, ausgaben=ausgaben)
@app.route("/auswertung/endabrechnung_event")
def endabrechnung_event():
    events = Event.query.order_by(Event.datum.desc()).all()
    selected_event_id = request.args.get("event_id", type=int)
    daten = {}

    if selected_event_id:
        event = Event.query.get_or_404(selected_event_id)

        # Getränkeumsatz
        umsatz = (
            db.session.query(func.sum(Getraenk.preis))
            .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
            .join(TeilnehmerEvent, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .filter(TeilnehmerEvent.event_id == selected_event_id)
            .scalar() or 0.0
        )

        # Einnahmen
        einnahmen = (
            db.session.query(func.sum(Einnahme.betrag))
            .filter(Einnahme.event_id == selected_event_id)
            .scalar() or 0.0
        )

        # Ausgaben (Details + Summe)
        ausgaben = (
            db.session.query(Ausgabe.kategorie, Ausgabe.beschreibung, Ausgabe.betrag)
            .filter(Ausgabe.event_id == selected_event_id)
            .order_by(Ausgabe.datum)
            .all()
        )
        summe_ausgaben = sum(ausgabe[2] for ausgabe in ausgaben)

        # Ergebnis
        gewinn = einnahmen + umsatz - summe_ausgaben

        daten = {
            "event": event,
            "umsatz": umsatz,
            "einnahmen": einnahmen,
            "ausgaben": ausgaben,
            "summe_ausgaben": summe_ausgaben,
            "gewinn": gewinn
        }

    return render_template("endabrechnung_event.html", events=events, selected_event_id=selected_event_id, daten=daten)
@app.route("/auswertung/endabrechnung_jahr")
def endabrechnung_jahr():
    # Alle Jahre mit Verkäufen
    jahre = (
        db.session.query(func.strftime('%Y', Event.datum))
        .group_by(func.strftime('%Y', Event.datum))
        .order_by(func.strftime('%Y', Event.datum))
        .all()
    )

    daten = []

    for jahr_tuple in jahre:
        jahr = jahr_tuple[0]

        # Alle Events des Jahres
        events = (
            db.session.query(Event.id)
            .filter(func.strftime('%Y', Event.datum) == jahr)
            .all()
        )
        event_ids = [e.id for e in events]

        # Getränkeumsatz
        umsatz = (
            db.session.query(func.sum(Getraenk.preis))
            .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
            .join(TeilnehmerEvent, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .filter(TeilnehmerEvent.event_id.in_(event_ids))
            .scalar() or 0.0
        )

        # Einnahmen
        einnahmen = (
            db.session.query(func.sum(Einnahme.betrag))
            .filter(Einnahme.event_id.in_(event_ids))
            .scalar() or 0.0
        )

        # Ausgaben
        ausgaben = (
            db.session.query(func.sum(Ausgabe.betrag))
            .filter(Ausgabe.event_id.in_(event_ids))
            .scalar() or 0.0
        )

        gewinn = einnahmen + umsatz - ausgaben

        daten.append({
            "jahr": jahr,
            "umsatz": umsatz,
            "einnahmen": einnahmen,
            "ausgaben": ausgaben,
            "gewinn": gewinn
        })

    return render_template("endabrechnung_jahr.html", daten=daten)
@app.route("/export/endabrechnung_event/pdf")
def export_endabrechnung_event_pdf():
    event_id = request.args.get("event_id", type=int)
    if not event_id:
        return redirect(url_for("endabrechnung_event"))

    event = Event.query.get_or_404(event_id)

    # Getränkeumsatz
    umsatz = (
        db.session.query(func.sum(Getraenk.preis))
        .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
        .join(TeilnehmerEvent, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
        .filter(TeilnehmerEvent.event_id == event_id)
        .scalar() or 0.0
    )

    # Einnahmen
    einnahmen = (
        db.session.query(func.sum(Einnahme.betrag))
        .filter(Einnahme.event_id == event_id)
        .scalar() or 0.0
    )

    # Ausgaben
    ausgaben = (
        db.session.query(Ausgabe.kategorie, Ausgabe.beschreibung, Ausgabe.betrag)
        .filter(Ausgabe.event_id == event_id)
        .order_by(Ausgabe.datum)
        .all()
    )
    summe_ausgaben = sum(a[2] for a in ausgaben)
    gewinn = einnahmen + umsatz - summe_ausgaben

    html = render_template("endabrechnung_event_pdf.html", event=event, umsatz=umsatz, einnahmen=einnahmen, ausgaben=ausgaben, summe_ausgaben=summe_ausgaben, gewinn=gewinn)

    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=endabrechnung_event_{event_id}.pdf'
    return response
@app.route("/export/endabrechnung_jahr/pdf")
def export_endabrechnung_jahr_pdf():
    jahre = (
        db.session.query(func.strftime('%Y', Event.datum))
        .group_by(func.strftime('%Y', Event.datum))
        .order_by(func.strftime('%Y', Event.datum))
        .all()
    )

    daten = []

    for jahr_tuple in jahre:
        jahr = jahr_tuple[0]
        event_ids = [e.id for e in Event.query.filter(func.strftime('%Y', Event.datum) == jahr).all()]

        umsatz = (
            db.session.query(func.sum(Getraenk.preis))
            .join(Verkauf, Verkauf.getraenk_id == Getraenk.id)
            .join(TeilnehmerEvent, Verkauf.teilnehmer_event_id == TeilnehmerEvent.id)
            .filter(TeilnehmerEvent.event_id.in_(event_ids))
            .scalar() or 0.0
        )

        einnahmen = (
            db.session.query(func.sum(Einnahme.betrag))
            .filter(Einnahme.event_id.in_(event_ids))
            .scalar() or 0.0
        )

        ausgaben = (
            db.session.query(func.sum(Ausgabe.betrag))
            .filter(Ausgabe.event_id.in_(event_ids))
            .scalar() or 0.0
        )

        gewinn = einnahmen + umsatz - ausgaben

        daten.append({
            "jahr": jahr,
            "umsatz": umsatz,
            "einnahmen": einnahmen,
            "ausgaben": ausgaben,
            "gewinn": gewinn
        })

    html = render_template("endabrechnung_jahr_pdf.html", daten=daten)

    pdf_puffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf_puffer)

    if pisa_status.err:
        return f"Fehler beim Erstellen des PDFs: {pisa_status.err}"

    response = make_response(pdf_puffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=endabrechnung_pro_jahr.pdf'
    return response
