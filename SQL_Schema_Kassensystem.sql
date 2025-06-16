
-- Tabelle: Event
CREATE TABLE event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    datum DATE NOT NULL
);

-- Tabelle: Teilnehmer
CREATE TABLE teilnehmer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

-- Tabelle: Teilnehmer-Event-Zuordnung mit Bezahlstatus
CREATE TABLE teilnehmer_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    teilnehmer_id INTEGER NOT NULL,
    bezahlt_status TEXT CHECK (bezahlt_status IN ('offen', 'bezahlt', 'twint', 'schuld')) DEFAULT 'offen',
    FOREIGN KEY (event_id) REFERENCES event(id),
    FOREIGN KEY (teilnehmer_id) REFERENCES teilnehmer(id)
);

-- Tabelle: Getränk
CREATE TABLE getraenk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    preis REAL NOT NULL,
    kategorie TEXT
);

-- Tabelle: Verkauf
CREATE TABLE verkauf (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teilnehmer_event_id INTEGER NOT NULL,
    getraenk_id INTEGER NOT NULL,
    zeitpunkt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teilnehmer_event_id) REFERENCES teilnehmer_event(id),
    FOREIGN KEY (getraenk_id) REFERENCES getraenk(id)
);

-- Tabelle: Ausgaben
CREATE TABLE ausgabe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    betrag REAL NOT NULL,
    kategorie TEXT,
    beschreibung TEXT,
    datum DATE NOT NULL,
    FOREIGN KEY (event_id) REFERENCES event(id)
);

-- Tabelle: Einnahmen (z. B. Bargeld, Twint)
CREATE TABLE einnahme (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    betrag REAL NOT NULL,
    zahlungsmethode TEXT,
    kommentar TEXT,
    datum DATE NOT NULL,
    FOREIGN KEY (event_id) REFERENCES event(id)
);
