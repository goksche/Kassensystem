@echo off
REM Python-App starten
start cmd /k "python run.py"

REM Warten, damit die App hochfährt (optional)
timeout /t 5 /nobreak

REM Webseite im Standardbrowser öffnen
start http://127.0.0.1:5000
