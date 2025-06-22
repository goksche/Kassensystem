# Kassensystem

A simple event-based cashier system built with Python and Flask. It manages events, participants and beverage sales while generating overviews and reports in CSV or PDF format. Data is stored in a local SQLite database.

## Setup

1. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**
   ```bash
   python run.py
   ```
   The database `instance/kassensystem.sqlite` is created automatically on the first start.

## Database initialization

To reset or manually create the database run:
```bash
python -m app.datenbank
```
The script asks for confirmation before dropping existing tables and recreating them.

## Configuration

Settings are loaded from `config.py`. The following environment variable is supported:

- `SECRET_KEY` – Flask secret key used for sessions. Defaults to `"change-me"`.

## Environment

- Python 3.11+
- Flask 2.3.3
