# 📋 VibeSpool Development Backlog

## ✅ Abgeschlossen (v2.3.0 - "The Custom Label & Project Module Update")
- [x] **🏷️ Eigene Label-Größe & dynamische Skalierung:** Breite und Höhe in mm im Label Creator konfigurierbar, inklusive proportionaler Skalierung (Schriften und QR-Code), automatischer Orientierungsanpassung (Horizontal/Vertikal) und verzerrungsfreier Live-Vorschau.
- [x] **👁️ System-Vorschau für Labels:** Neues Feature zum schnellen Öffnen eines hochauflösenden Label-Entwurfs direkt im Standard-Bildbetrachter des Betriebssystems vor dem Drucken.
- [x] **📄 DPI-korrekter PDF-Export:** Skaliert Labelraster im DIN A4-Export auf 300 DPI und Rollen-Labels im 1-Label-pro-Seite Modus auf exakte Millimeter-Abmessungen via 254.0 DPI (10px/mm).
- [x] **📂 Globaler Druckverlauf / Projektverwaltung:** Modular aktivierbare Projektverwaltung zur Organisation von Druckaufträgen in Gruppen, Ordnern und Unterordnern (z. B. `Litophane / runde`). Muss in den Optionen erst aktiviert werden. Standardmäßig sind keine Projekte aktiv. 
- [x] **📊 Aggregierte Projekt-Statistiken:** Rekursive Aufsummierung von Auftragsanzahl, Filamentgewicht, Druckzeit und Kosten/Umsatz direkt im Projekt-Fenster und in einem neuen "Projekte"-Tab innerhalb des Finanz-Dashboard.

## ✅ Abgeschlossen (v2.2.2 - "The Search & Custom ID Patch")
- [x] **🧮 Quick-Cost Alphanumeric-ID-Fix:** Die Preisermittlung funktioniert nun auch bei selbst angelegten, alphanumerischen Spulen-IDs (z. B. `PLA-01`) fehlerfrei durch Umstellung der Regex-Filterung auf einen flexiblen Split-Mechanismus.
- [x] **🔍 Suchfunktion im Quick-Cost Rechner:** Spulenauswahl über ein neues, integriertes Suchfeld oberhalb des Dropdowns filtern, statt durch lange Listen scrollen zu müssen.
- [x] **🔍 Suchfunktion im Auftragsplaner:** Spulen in der Spulen-Auswahl für neue Aufträge über ein Suchfeld filtern und per Enter-Taste direkt zum Auftrag hinzufügen.

## ✅ Abgeschlossen (v2.2.0 - "The Multi-Printer, Custom Location & Smart-Match Update")
- [x] **🤖 Multi-Drucker-Verwaltung:** Dynamische Liste von Druckern (Bambu Lab & Klipper) in den Einstellungen anlegen, bearbeiten und löschen.
- [x] **🔌 AMS- & Spulen-Zuordnung pro Drucker:** Zuweisung von globalen AMS-Einheiten an bestimmte Drucker sowie Definition eines standardmäßigen Lagerorts (z. B. `P1S 2 Extern`) für die externe Spule.
- [x] **🧠 Intelligenteres Smart-Match (Cloud & Live-Sync):** Automatische und fehlerfreie Zuweisung von Druckjobs zu dem jeweiligen Drucker und seinen Slots (behebt die falsche Anzeige von `AMS 64 Slot 4` für die externe Spule `255`).
- [x] **🏠 Visualisierung leerer Zusatz-Orte:** Benutzerdefinierte Lagerorte werden im Regal-Visualisierer nun immer angezeigt (auch wenn sie leer sind), um Drag & Drop dorthin zu ermöglichen.
- [x] **🔄 Quick-Swap-Erweiterung:** Quick-Swap-Dialog um alle benutzerdefinierten Orte und das globale LAGER erweitert, ohne unerwünschte Spulenverdrängung bei unbeschränkten Zielen.
- [x] **⚡ Druckerspezifische Strom- & Verschleißkosten:** Konfiguration von Watt und Verschleiß pro Drucker im Settings-Editor, die prioritär im Smart-Match-Abzug verwendet werden.
- [x] **🖱️ Drag & Drop Auto-Scroll-Fix:** Robuster Scroll-Check im ShelfVisualizer und direktes Ausblenden des Vorschaufensters, um clunky Verhalten zu beheben.
- [x] **📋 Drucker-Auswahl & Kalkulation bei Aufträgen:** Auswahl des Druckers in der Warteschlange zur präzisen Kostenschätzung und zum verbrauchsabhängigen Abzug.
- [x] **🧮 Drucker-Auswahl im Quick-Cost Rechner:** Live-Kalkulation der Kosten basierend auf druckerspezifischen Parametern direkt im Schnellrechner.
- [x] **📊 Globale Druckhistorie-Aggregation:** Automatische Zusammenführung und Berechnung der tatsächlichen Druckkosten über alle Drucker hinweg.
- [x] **🧮 Quick-Cost Spulenpreis-Fix:** Zuverlässige Übernahme des Spulenpreises bei String-ID-Spulen.
- [x] **📋 Job-Abzug Layout-Fix:** Scrollbare Ansicht und sichtbare Buttons im Dialog "Erledigt & Abziehen".

## ✅ Abgeschlossen (v2.1.2 - "The Slicer, Time Split & Dashboard Filter Update")
- [x] **⏱️ Stunden/Minuten-Eingabe:** Präzise Eingabe von Stunden und Minuten bei Druckzeiten im Auftragsplaner und Job-Abzug (keine reinen Dezimalzahlen mehr).
- [x] **📂 3MF-Slicer-Import:** Direktes Auslesen der Druckzeit und des Filamentgewichts aus `.3mf`-Dateien (Metadata/slice_info.config von Bambu/OrcaSlicer) mit neuem verständlichen Hinweis bei unsliced Modelldateien.
- [x] **📊 Responsive Analytics & Dashboard-Filter:** Filter-Bar für Hersteller, Material und Farbe im Analytics-Dashboard. KPIs, Verbrauchs-Diagramm und globale Historie reagieren live auf Filter. 4 neue Tabs (Material, Hersteller, Farbe, Detailliert).
- [x] **🎨 Farb-Mapping & Modifikator-Shading:** Sofortige Konvertierung von eingegebenen Hexcodes (z.B. `#FFFF00`) in Farbnamen. Dynamische Berechnung von Farb-Schattierungen (z.B. dunkelblau, hellgrün, jadeweiß, silk rot) zur Vermeidung von unerwünschten zweifarbigen Spulen-Darstellungen.

## ✅ Abgeschlossen (v2.1.1 - "The Planner, Quick Cost & Visualizer Update")
- [x] **📝 Flexibler Auftragsplaner:** Zuweisung mehrerer Spulen mit individueller Grammvorgabe und geplanter Druckzeit sowie Live-Preisanzeige. Pre-fill beim anschließenden Abzug.
- [x] **🧮 Multi-Spool Quick Cost:** Der Schnellrechner unterstützt nun beliebig viele Spulenzeilen.
- [x] **🤖 AMS Pinning:** Optionale Fixierung der AMS-Einheiten am oberen Fensterrand im Regal-Visualisierer (persistiert in Einstellungen).
- [x] **📊 Finanz-Grouping:** Kombinierte Aggregations-Ansichten (z.B. Marke & Farbe) im Bestands-Dashboard.

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