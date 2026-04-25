# 📋 VibeSpool Development Backlog

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

## 🚀 Priorität 1: Next Steps (v2.1.0)
- [ ] **📚 Globale Filament-Datenbank (Bake-in):** Integrierte Datenbank für bekannte Hersteller-Filamente, die per Klick (inkl. Leergewicht und Shop-Link) ins eigene Lager kopiert werden können.
- [ ] **🎨 Custom Label Designer:** Baukasten zum freien Gestalten von Etiketten (Logos hinzufügen, Schriftarten ändern).

## 🔮 Langzeit-Vision (v3.0)
- [ ] **📂 3MF Deep-Dive FTP Parsing:** Automatisches Auslesen der Gewichte pro Slot direkt vom Drucker-Speicher.