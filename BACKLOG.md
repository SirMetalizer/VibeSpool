# 📋 VibeSpool Backlog & Roadmap

Diese Liste enthält alle geplanten Features, Verbesserungen und bekannten Bugs, die durch das Feedback der Community gesammelt wurden. 

## 🚨 Priorität 1: Kritische Bugs (Next Patch)
- [X] **ID-Crash verhindern:** Das ID-Feld muss auf `readonly` gesetzt werden. Die manuelle Vergabe von bereits existierenden IDs führt aktuell zu einem kompletten Absturz beim Laden der Tabelle ("Item 20 already exists").
- [X] **Ghost-Fenster Fix:** Beim Schließen der App über das "X" bleibt der Hintergrundprozess manchmal aktiv. Ein harter `sys.exit()` oder sauberes Thread-Handling muss beim `on_closing` Event implementiert werden.
- [X] **Eingabe-Validierung ("Toter Button"):** Wenn falsche Datentypen (z.B. Text in ein Zahlenfeld) eingegeben werden, passiert beim Klick auf "Neu Hinzufügen" nichts. Hier muss ein Warn-Popup (`try/except`) ergänzt werden.

## 💅 Priorität 2: UI/UX & Quick Wins
- [X] **Farb- & Finish-Listen aufräumen:** "Glow in Dark", "Transparent" und "Translucent" aus den Farben entfernen und stattdessen in die "Finish/Effekt"-Kategorie verschieben.
- [X] **Begriff "Finish" umbenennen:** Zur besseren Verständlichkeit in "Typ/Effekt" oder "Eigenschaft" umbenennen.
- [X] **Darkmode Scrollbalken:** Die Sichtbarkeit der Scrollbalken im Dark-Theme über das `ttk.Style` Mapping verbessern.
- [X] **Mausrad-Fix:** Das Scrollen im `Treeview` (Tabelle) robuster machen, sodass es auch reagiert, wenn die Maus nicht exakt auf einer Zeile schwebt.
- [X] **Slicer-Verbrauch abziehen:** Ein kleines Eingabefeld hinzufügen, um den vom Slicer berechneten Verbrauch direkt vom aktuellen Brutto-Gewicht abzuziehen.

## 🚀 Priorität 3: Neue Features (Version 2.0)
- [X] **Excel / CSV Import:** Funktion hinzufügen, um bestehende Filament-Lagerlisten aus `.csv`-Dateien in die VibeSpool-Datenbank zu importieren.
- [X] **Individuelle Regal-Beschriftungen:** Im Regal-Planer die Möglichkeit schaffen, Fächern einen festen Namen zu geben (z.B. "Fach 1 (Bambu PLA)").
- [X] **Erweiterbare Materialien & Farben:** Die hart codierten Listen (PLA, PETG...) in die Settings auslagern, sodass Nutzer eigene Materialien (z.B. PA-CF, GF) und Farbkombinationen (Tri-Color) hinzufügen können.
- [ ] **Hersteller- & Tara-Verknüpfung:** Das Hersteller-Feld von Freitext in ein Dropdown umwandeln und idealerweise direkt mit den Leerspulen-Profilen verknüpfen.

**UI & Visualisierung**
- [X] **Material in Regal-Ansicht:** In der grafischen Regal- und AMS-Ansicht (`ShelfVisualizer`) das Material (PLA, PETG etc.) direkt auf der Spulen-Kachel anzeigen, nicht erst beim Mouse-Over (Tooltip).
- [X] **Dual- / Tri-Color Support:** Das Farb-Dropdown im Hauptfenster erweitern, sodass bei mehrfarbigen Filamenten 2 oder 3 Farben (inkl. Hex-Codes) ausgewählt und auf dem Icon gespalten dargestellt werden können.

**Workflow & Synchronisation**
- [X] **AMS Auto-Import:** Wenn der Bambu AMS-Sync eine Spule erkennt (z.B. via Bambu RFID), die noch nicht in der VibeSpool-Datenbank existiert, einen Button anbieten, um diese direkt inkl. erkannter Farbe und Material als neue Spule ins Lager zu importieren.
- [X] **Hex-Codes in Listen-Manager:** Im neuen Einstellungs-Tab "Listen" einen Color-Picker ergänzen, damit Nutzer nicht nur Farbnamen (z.B. "Bambu Rot"), sondern echte Hex-Werte (`#FF0000`) sauber und einfach in ihre benutzerdefinierten Listen einspeichern können.
- [X] **Globale Kollisionsprüfung (Regal & AMS):** Beim manuellen Verschieben einer Spule über das Hauptformular oder den Quick-Swap (egal ob vom AMS ins Regal, vom Regal ins AMS oder innerhalb des Regals) prüfen, ob der Ziel-Platz bereits durch eine andere aktive Spule belegt ist. Falls ja: Warnung ausgeben und heimliches Überschreiben verhindern.

**Datenbank & Vorlagen**
- [X] **Spulen-Vorlagen erweitern:** Die Standardspule für "Geeetech" mit dem passenden Leergewicht in die festen Vorlagen (`spool_presets.py`) aufnehmen. Liste durch weitere Hersteller ergänzen, um die Auswahl zu erleichtern.

## 🔮 Priorität 4: Langzeit-Visionen & Integrationen
- [ ] **Anycubic Integration:** Recherche nach lokalen oder inoffiziellen Cloud-APIs zur Anbindung von Anycubic-Druckern.
- [ ] **One-Window Dashboard:** Abkehr von Popups hin zu einer integrierten, modernen Dashboard-Ansicht im Hauptfenster.
- [ ] **Mehrsprachigkeit (Internationalisierung / i18n):** Das Programm für eine internationale Nutzerschaft vorbereiten. Feste UI-Texte in Sprachdateien (z.B. `en.json`, `de.json`) auslagern, sodass Nutzer die Sprache in den Optionen umschalten können (Fokus zunächst auf Englisch).