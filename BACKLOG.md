# 📋 VibeSpool Backlog & Roadmap

Diese Liste enthält alle geplanten Features, Verbesserungen und bekannten Bugs, die durch das Feedback der Community gesammelt wurden. 

## 🚨 Priorität 1: Kritische Bugs (Next Patch)
- [ ] **ID-Crash verhindern:** Das ID-Feld muss auf `readonly` gesetzt werden. Die manuelle Vergabe von bereits existierenden IDs führt aktuell zu einem kompletten Absturz beim Laden der Tabelle ("Item 20 already exists").
- [ ] **Ghost-Fenster Fix:** Beim Schließen der App über das "X" bleibt der Hintergrundprozess manchmal aktiv. Ein harter `sys.exit()` oder sauberes Thread-Handling muss beim `on_closing` Event implementiert werden.
- [ ] **Eingabe-Validierung ("Toter Button"):** Wenn falsche Datentypen (z.B. Text in ein Zahlenfeld) eingegeben werden, passiert beim Klick auf "Neu Hinzufügen" nichts. Hier muss ein Warn-Popup (`try/except`) ergänzt werden.

## 💅 Priorität 2: UI/UX & Quick Wins
- [ ] **Farb- & Finish-Listen aufräumen:** "Glow in Dark", "Transparent" und "Translucent" aus den Farben entfernen und stattdessen in die "Finish/Effekt"-Kategorie verschieben.
- [ ] **Begriff "Finish" umbenennen:** Zur besseren Verständlichkeit in "Typ/Effekt" oder "Eigenschaft" umbenennen.
- [ ] **Darkmode Scrollbalken:** Die Sichtbarkeit der Scrollbalken im Dark-Theme über das `ttk.Style` Mapping verbessern.
- [ ] **Mausrad-Fix:** Das Scrollen im `Treeview` (Tabelle) robuster machen, sodass es auch reagiert, wenn die Maus nicht exakt auf einer Zeile schwebt.
- [ ] **Slicer-Verbrauch abziehen:** Ein kleines Eingabefeld hinzufügen, um den vom Slicer berechneten Verbrauch direkt vom aktuellen Brutto-Gewicht abzuziehen.

## 🚀 Priorität 3: Neue Features (Version 2.0)
- [ ] **Excel / CSV Import:** Funktion hinzufügen, um bestehende Filament-Lagerlisten aus `.csv`-Dateien in die VibeSpool-Datenbank zu importieren.
- [ ] **Individuelle Regal-Beschriftungen:** Im Regal-Planer die Möglichkeit schaffen, Fächern einen festen Namen zu geben (z.B. "Fach 1 (Bambu PLA)").
- [ ] **Erweiterbare Materialien & Farben:** Die hart codierten Listen (PLA, PETG...) in die Settings auslagern, sodass Nutzer eigene Materialien (z.B. PA-CF, GF) und Farbkombinationen (Tri-Color) hinzufügen können.
- [ ] **Hersteller- & Tara-Verknüpfung:** Das Hersteller-Feld von Freitext in ein Dropdown umwandeln und idealerweise direkt mit den Leerspulen-Profilen verknüpfen.

## 🔮 Priorität 4: Langzeit-Visionen & Integrationen
- [ ] **Anycubic Integration:** Recherche nach lokalen oder inoffiziellen Cloud-APIs zur Anbindung von Anycubic-Druckern.
- [ ] **One-Window Dashboard:** Abkehr von Popups hin zu einer integrierten, modernen Dashboard-Ansicht im Hauptfenster.