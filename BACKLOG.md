# 📋 VibeSpool Development Backlog

## ✅ Abgeschlossen (v2.1.0 - "The Finance, Archive & Scroll Update")
- [x] **📊 Finanzen Hersteller & Farbe:** Neues Register im Analytics-Dashboard für Gruppierung nach Marke und bereinigter Farbe, inklusive interaktiver Sortierung aller Tabellenspalten.
- [x] **📦 Responsive Auto-Scroll:** Canvas-Ansichten scrollen nun vollautomatisch mit, wenn eine Spule per Drag & Drop nahe an den Fensterrand gezogen wird.
- [x] **📝 Auftrags-Archiv & Bilder:** Aufteilung des Auftragsplaners in "Warteschlange" und "Archiv", und Möglichkeit, Modellbilder für Druckaufträge hinzuzufügen (automatisch komprimiert auf 600x600 px).
- [x] **📜 Logbuch-Editierfunktion:** Doppelklick im Spulen-Logbuch öffnet nun einen Editierbereich mit integrierten Materialkosten- und Gewinnmargen-Rechnern.

## ✅ Abgeschlossen (v2.0.4 - "The Apple Design & Code Refactoring Update")
- [x] **🎨 Apple Look Design:** Vollständiger optischer Overhaul im cleanen "Apple Look" (Light: `#F2F2F7`, Dark: `#1C1C1E`, Accent: `#007AFF`). Schutz vor "Ostfriesen-Bug" durch Kontrast-Absicherung für alle Eingaben, Text-Boxen und Dropdowns.
- [x] **📂 Modularisierung:** Extraktion von 10 Toplevel-Dialogen aus der monolithischen `filament_gui.py` in das `core`-Verzeichnis zur Verbesserung der Wartbarkeit.

## ✅ Abgeschlossen (v2.0.3 - "The Time Machine & Security Update")
- [x] **🔐 Sicherer Browser-Login (OAuth2):** Umstellung der Bambu-API auf den offiziellen MakerWorld-Login via Webbrowser (Port 8080 Listener).
- [x] **🕰️ Smart AMS Memory:** Hintergrund-Snapshots der AMS-Belegung in `ams_snapshots.json`. Cloud-Syncs suchen nun nach historischen AMS-Belegungen.
- [x] **📝 Print-Queue Flexibilität:** Aufträge können nun als "Erledigt" markiert werden, ohne dass Filament aus dem Lager abgezogen wird.
- [x] **📦 Professionelles Windows Setup:** Umstellung der portablen `.exe` auf einen echten Windows-Installer (via Inno Setup) inkl. Startmenü-Einträgen und Desktop-Icon.
- [x] **🌈 Rainbow-Farben:** Dynamisches Generieren von 6-farbigen Icons für Spulen mit dem Namen "Rainbow" oder "Regenbogen".

## ✅ Abgeschlossen (v2.0.1 - "The Pop-up Killer & Print Queue Update")
- [x] **UX-EVALUATION & Refactoring:** Pop-up-Fenster in dynamische, verschiebbare Side-Panels (PanedWindow) umgebaut, um die "Pop-up-Flut" zu stoppen.
- [x] **Lager-Logik (Grid-Naming V2):** Raster-basiertes Naming für Regal-Fächer UND Slots inkl. magischer Hintergrund-Umbuchung von Spulen.
- [x] **📝 Auftrags-Planer (Print Queue & MES):** Neues Planungs-Tool für kommende Drucke. Zuweisung von Kunde/Titel, Modell-Links, Spulen und Notizen.
- [x] **BUGFIX:** Nozzle- und Bed-Temp Felder verdoppeln ihre Werte beim Laden nicht mehr.
- [x] **UX-FIX:** Systematische Prüfung aller Pop-up-Fenster: Buttons hart an den unteren Rand gekoppelt.

## ✅ Abgeschlossen (v2.0.0 - "The Cost Center & Enterprise Update")
- [x] **Globales Cost Center:** Vollständige Historie aller Drucke.
- [x] **Gewerbe-Kalkulation (Marge & Verschleiß):** Berechnung von Maschinenabnutzung und Marge.
- [x] **Auto-Heal & Retro-Fit:** Einträge in der Historie können nachträglich bearbeitet werden.
- [x] **Individuelles Leergewicht (Einweg-Spulen)**
- [x] **Omni-Live-Suche**
- [x] **🧮 Quick-Cost Rechner**

## 🚀 Priorität 1: Next Steps (v2.2.0)
- [ ] **📚 Globale Filament-Datenbank (Bake-in):** Integrierte Datenbank für bekannte Hersteller-Filamente, die per Klick (inkl. Leergewicht und Shop-Link) ins eigene Lager kopiert werden können.
- [ ] **🎨 Custom Label Designer:** Baukasten zum freien Gestalten von Etiketten (Logos hinzufügen, Schriftarten ändern).

## 🔮 Langzeit-Vision (v3.0)
- [ ] **📂 3MF Deep-Dive FTP Parsing:** Automatisches Auslesen der Gewichte pro Slot direkt vom Drucker-Speicher.