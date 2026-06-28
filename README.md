# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-2.3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** VibeSpool ist ein lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle, mobile und kaufmännische Kontrolle über deine Spulen gibt.

<img width="1924" height="1044" alt="VibeSpool Main Dashboard" src="https://github.com/user-attachments/assets/7234891c-0458-478b-8c5a-7d9e6cd184cb" />
---

## 🆕 Was ist neu in Version 2.3.0? ("The Custom Label & Project Module Update")
Dieses Update bringt maximale Freiheit beim Etikettendruck durch frei konfigurierbare Label-Größen mit proportionaler Skalierung, eine direkte System-Vorschau und DPI-genauen PDF-Export sowie eine mächtige, modular aktivierbare Projektverwaltung zur strukturierten Organisation und Kosten-Aggregation deiner Druckaufträge!

### ✨ Die Highlights:

* **🤖 Multi-Drucker-Verwaltung:** Dynamische Liste von Druckern (Bambu Lab, Klipper/Moonraker oder Manuell) in den Einstellungen erstellen, bearbeiten und löschen.
* **🔌 AMS- & Spulen-Zuordnung pro Drucker:** Weise AMS-Einheiten und externe Spulenplätze (z. B. `P1S 2 Extern`) bestimmten Druckern zu, um deinen Filamentbestand optimal zu strukturieren.
* **🧠 Intelligenteres Smart-Match & Aggregation:** Cloud- und Live-Syncs ordnen Verbräuche exakt den druckerspezifischen Slots zu. Die globale Druckhistorie aggregiert Kosten und Verbräuche über alle Drucker hinweg.
* **⚡ Druckerspezifische Strom- & Verschleißkosten:** Konfiguriere Leistung (Watt) und Verschleiß (pro Stunde) individuell pro Drucker für eine centgenaue Kalkulation bei Aufträgen und im Quick-Cost Rechner.
* **📐 Fenstergröße- & Positions-Speicherung:** Alle Dialogfenster (Hauptfenster, Aufträge, Finanzen, Spulendatenbank, Labels, Einkaufsliste und Flussrechner) merken sich nun ihre Größe und Position – sowohl beim Schließen über das "X" als auch über Buttons im Dialog.
* **📦 Regal-Optimierungen & Rechtsklick-Menü:**
  * **Neues Kontextmenü:** Rechtsklick auf Spulen im Regal ermöglicht Quick-Swap, Löschen, Klonen, Öffnen des Spulen-Logbuchs und mehr (inklusive automatischem Filter-Reset).
  * **Leere Zusatz-Orte:** Freie, benutzerdefinierte Standorte werden nun im Regal visualisiert, um leere Slots als Drag & Drop-Ziele anzubieten.
  * **Scrollbar-Intelligenz:** Der horizontale Scrollbalken sperrt sich automatisch, wenn der Inhalt komplett sichtbar ist, und schaltet sich erst bei Überlauf aktiv.
  * **37 Kerntests:** 37 Unit-Tests sichern nun die Stabilität der Kernfunktionen dauerhaft ab.

* **🏷️ Eigene Label-Größe & dynamische Skalierung:** Breite und Höhe sind im Label Creator in mm konfigurierbar. Alle Texte und der QR-Code skalieren proportional mit. Je nach Seitenverhältnis passt sich die Orientierung (Horizontal/Vertikal) automatisch an.
* **👁️ System-Vorschau für Labels:** Öffne den hochauflösenden Label-Entwurf mit nur einem Klick direkt im Standard-Bildbetrachter deines Betriebssystems vor dem eigentlichen Druck.
* **📄 DPI-korrekter PDF-Export:** Skaliert Labelraster im DIN A4-Export auf 300 DPI und Rollen-Labels im 1-Label-pro-Seite Modus auf exakte Millimeter-Abmessungen via 254.0 DPI (10px/mm) zur Vermeidung von Verzerrungen.
* **📂 Globaler Druckverlauf & Projektverwaltung:** Organisiere Druckaufträge in Gruppen, Ordnern und Unterordnern (z. B. `Litophane / runde`). Das Projektmodul lässt sich in den Einstellungen flexibel aktivieren und ist standardmäßig deaktiviert.
* **📊 Aggregierte Projekt-Statistiken:** Rekursive Aufsummierung von Auftragsanzahl, verbrauchtem Filamentgewicht, Druckzeit sowie Kosten und Umsätzen direkt im Projekt-Fenster und in einem neuen "Projekte"-Tab innerhalb des Finanz-Dashboards.


---

## ✨ Weitere Features (Detail-Ansicht)

### ☁️ Bambu Cloud API & Smart-Match
Verbinde VibeSpool mit der Bambu Cloud. Das System lädt deine fertigen Druckaufträge herunter, erkennt automatisch, welche Spulen im AMS verwendet wurden (**Smart-Match**) und teilt den Verbrauch bei Multi-Color-Drucken grammgenau auf.

<img width="1014" height="805" alt="image" src="https://github.com/user-attachments/assets/aa1822b7-382e-4503-b4f0-0906a73616a3" />

### 📝 Auftrags-Planer (Print Queue & MES)
VibeSpool wird zur Schaltzentrale deiner Druck-Aufträge! Mit dem Planungs-Tool kannst du anstehende Drucke verwalten. Weise Kunden oder Projekt-Titel zu, speichere direkte Links zu den 3D-Modellen und hinterlege genaue Notizen.

<img width="1068" height="747" alt="image" src="https://github.com/user-attachments/assets/720140a3-a733-4e17-bfdd-0f3322211ff3" />

### 💰 Das Cost Center (Gewerbe-Kalkulation)
VibeSpool berechnet nicht nur Material- und Stromkosten, sondern berücksichtigt auch Maschinenverschleiß (pro Druckstunde) und schlägt automatisch deine Gewinnmarge (%) auf. Alle Drucke über alle Spulen hinweg laufen im globalen Kassenbuch zusammen.

### 💰 Druckkosten-Rechner & Logbuch
VibeSpool kombiniert den Kaufpreis deiner Spulen mit deinem lokalen Strompreis und der Laufzeit des Drucks. Bei jedem Cloud-Sync siehst du auf den Cent genau, was dein Druck gekostet hat. Alles wird im **Spulen-Logbuch** dauerhaft als "Kontoauszug" gespeichert. In Version 2.1.0 lassen sich Logbucheinträge per Doppelklick korrigieren und mit einem Gewinnmargen-Rechner neu bewerten.

### 📊 Unified Analytics Dashboard
**Übersicht Finanzen:**

<img width="1096" height="888" alt="image" src="https://github.com/user-attachments/assets/d6087302-53c5-4680-8416-14f69bf809c8" />

**Druckhistorie aus der Bambu Cloud:**

<img width="853" height="641" alt="image" src="https://github.com/user-attachments/assets/882971f5-ac53-4c55-bd49-cd73ced4ca34" />

**Kostenrechner:**

<img width="964" height="697" alt="image" src="https://github.com/user-attachments/assets/d56dcd36-11d0-47f3-b1d6-358f7c92ffe7" />

### 📊 Unified Analytics & Auto-Heal Historie
Ein interaktives Dashboard zeigt dir den genauen Bestandswert, den Ø-Preis/kg und einen 7-Tage-Verbrauchsverlauf. Fehler beim Eintragen gemacht? Die Historie lässt sich nachträglich bearbeiten – VibeSpool repariert das Spulengewicht und das Chart automatisch (**Auto-Heal**).

### 📥 System-Tray & Hintergrund-Monitor
Schließe das Fenster und VibeSpool läuft lautlos im Windows-Tray (neben der Uhr) weiter. Es lauscht im Hintergrund auf deinen Drucker und meldet sich über smarte **Toast-Benachrichtigungen**.

### 📱 Mobile Companion & Handyscanner
VibeSpool wird kabellos! Scanne einfach den QR-Code am Monitor und dein Handy wird zum **kabellosen Handyscanner**.
* **Keine App-Installation:** Läuft direkt im Browser über deinen lokalen Webserver.
* **Hersteller-Barcodes:** Scanne Strichcodes von Originalverpackungen – VibeSpool lernt die Marken automatisch!

### ⚖️ Die Schlaue Waage
Nie wieder Leergewichte raten. Trage das Brutto-Gewicht ein, das deine Küchenwaage anzeigt. VibeSpool erkennt Hersteller und Material, zieht das korrekte Leerspulen-Gewicht ab und bucht das Netto-Gewicht ein.

### 📦 Lagerverwaltung & Doppeltiefe Regale
Bilde dein echtes Regal virtuell nach (z.B. 4 Reihen, 8 Spalten). VibeSpool unterstützt sogar **doppeltiefe Regale** (2 Spulen hintereinander) und bietet eine **Quick-Swap** Funktion, um Spulen blitzschnell ins AMS zu tauschen. Die Regalansicht scrollt bei Drag & Drop vollautomatisch mit.

### 🏷️ Etiketten-Druck & Label Creator
Generiere automatisch fertige Etiketten mit QR-Codes, Drucktemperaturen und Farben. Exportiere sie als PNG oder direkt als **PDF-Bögen** für DIN A4 oder Rollen-Etikettendrucker.

### 🤖 Bambu AMS Live-Sync via MQTT
Gleiche dein Lager live im lokalen Netzwerk mit deinem Bambu Lab AMS ab. VibeSpool liest aus, welche Farbe und welches Material aktuell in welchem Slot steckt.

### 📋 Listen-Verwaltung & CSV-Import
Füge eigene Materialien (z.B. PAHT-CF), Farben oder Effekte flexibel hinzu. Importiere deine alten Excel-Tabellen bequem über die integrierte CSV-Schnittstelle.

---

## 🚀 Installation & Start

### Für Nutzer (Windows & Mac)
1. Lade dir die neuste Version unter [Releases](https://github.com/SirMetalizer/VibeSpool/releases/latest) herunter.
2. Starte die **`VibeSpool_Win.exe`** (oder `.app` auf dem Mac) – keine Installation von Python nötig!

### Für Entwickler
Stelle sicher, dass **Python 3.10+** installiert ist.

1. **Repository klonen:**

  ```bash
  git clone https://github.com/SirMetalizer/VibeSpool.git
  cd VibeSpool
  ```

Abhängigkeiten installieren:

   ```bash
   pip install Pillow pyzbar opencv-python qrcode paho-mqtt requests
   ```
Starten:

   ```bash
   python filament_gui.py
   ```

---

## ⏳ Release-Historie

### 🆕 Was ist neu in Version 2.2.0? ("The Multi-Printer, Custom Location & Smart-Match Update")
* **🤖 Multi-Drucker-Verwaltung:** Dynamische Liste von Druckern (Bambu Lab & Klipper) in den Einstellungen anlegen, bearbeiten und löschen.
* **🔌 AMS- & Spulen-Zuordnung pro Drucker:** Zuweisung von globalen AMS-Einheiten an bestimmte Drucker sowie Definition eines standardmäßigen Lagerorts (z. B. `P1S 2 Extern`) für die externe Spule.
* **🧠 Intelligenteres Smart-Match:** Automatische Zuweisung von Druckjobs zu dem jeweiligen Drucker und seinen Slots.
* **🏠 Visualisierung leerer Zusatz-Orte:** Custom Lagerorte werden im Regal-Visualisierer nun immer angezeigt, um Drag & Drop dorthin zu ermöglichen.
* **🔄 Quick-Swap-Erweiterung:** Quick-Swap-Dialog um alle benutzerdefinierten Orte und das globale LAGER erweitert.
* **⚡ Druckerspezifische Strom- & Verschleißkosten:** Konfiguration von Watt und Verschleiß pro Drucker im Settings-Editor zur prioritären Verwendung im Smart-Match-Abzug.
* **📐 Fenstergröße- & Positions-Speicherung:** Alle Dialogfenster merken sich nun ihre Geometrie.
* **📋 Drucker-Auswahl & Kalkulation bei Aufträgen:** Auswahl des Druckers in der Warteschlange zur präzisen Kostenschätzung und zum verbrauchsabhängigen Abzug.
* **🧮 Drucker-Auswahl im Quick-Cost Rechner:** Live-Kalkulation der Kosten basierend auf druckerspezifischen Parametern direkt im Schnellrechner.
* **📊 Globale Druckhistorie-Aggregation:** Zusammenführung und Berechnung der tatsächlichen Druckkosten über alle Drucker hinweg.

### 🆕 Was ist neu in Version 2.1.1? ("The Planner, Quick Cost & Visualizer Customization Update")
* **📝 Flexiblerer Auftragsplaner:** Zuweisung mehrerer Spulen mit individueller Grammvorgabe und automatischer Preiskalkulation pro geplanter Druckzeit.
* **🧮 Quick-Cost Rechner V2:** Beliebig viele Spulenreihen und direkte Spulenauswahl aus dem Lagerbestand per Dropdown.
* **🔍 Symbolgröße & Zoom in der Regalansicht:** Dynamisches Skalieren (Klein, Mittel, Groß) inklusive Layout-Abständen und Schriftgrößen.
* **📌 Verbessertes AMS-Pinning:** Separater, abgegrenzter Bereich für fixierte AMS-Einheiten.
* **🔒 Stabile AMS-Sortierung:** Fixierung der AMS-Spulen in ihrer physischen Slot-Reihenfolge beim Sortieren der Tabelle.
* **📊 Kombinierte Finanz-Gruppierung:** Kombinationen wie "Hersteller & Farbe" im Dashboard.

### 🆕 Was ist neu in Version 2.1.0? ("The Finance, Archive & Scroll Update")
* **📊 Finanzen nach Hersteller & Farbe:** Im Analytics-Dashboard gibt es ein neues Register für die detaillierte Aufteilung nach Marke (Hersteller) und bereinigter Farbe. Sämtliche Tabellenspalten im Dashboard lassen sich jetzt per Klick interaktiv sortieren!
* **📝 Auftrags-Planer V2 (Archiv & Bilder):** Druckaufträge sind nun in eine aktive "Warteschlange" und ein "Archiv" für abgeschlossene Aufträge aufgeteilt. Du kannst Modellbilder hochladen (die automatisch ressourcenschonend komprimiert werden) und siehst diese direkt als Vorschau. Beim Abschließen werden Kosten und Verbrauch automatisch in das Spulen-Logbuch übernommen.
* **📜 Logbuch-Editor mit Preiskalkulatoren:** Einträge im Spulen-Logbuch können jetzt per Doppelklick editiert werden. Ein integrierter Rechner ermittelt dabei automatisch Materialkosten und Verkaufspreise basierend auf deiner gewünschten Gewinnmarge.
* **📦 Responsive Auto-Scroll:** Beim Drag & Drop von Spulen in der Regal- oder AMS-Ansicht scrollt das Fenster nun vollautomatisch mit, wenn du dich dem Fensterrand näherst. Perfekt für große Lager oder kleinere Monitore.

### 🆕 Was ist neu in Version 2.0.3? ("The Time Machine & Security Update")
* **🔐 Sicherer Browser-Login (OAuth2):** VibeSpool leitet euch nun auf die offizielle MakerWorld/BambuLab-Website im Browser weiter. (Voller Support für Google/Apple-Login & 2FA).
* **🕰️ Smart AMS Memory ("Die Zeitmaschine"):** VibeSpool speichert Hintergrund-Snapshots der AMS-Belegung, um den Verbrauch von älteren Cloud-Drucken akkurat abzubuchen.
* **📦 Echter Windows-Installer:** VibeSpool kommt jetzt mit einem professionellen Setup-Programm (`VibeSpool_Setup.exe`).
* **📝 Flexiblere Print-Queue:** Geplante Aufträge können jetzt mit "✅ Ohne Abzug erledigen" abgehakt werden.
* **🌈 Rainbow-Fix:** Spulen mit dem Namen "Rainbow" oder "Regenbogen" erhalten nun vollautomatisch ein schickes, sechsfarbiges Regenbogen-Icon.

### 🆕 Was ist neu in Version 1.10.0? ("The Smart Pro Update")
* **Bambu Cloud & Smart-Match:** Abzüge aus der Cloud werden jetzt vollautomatisch den richtigen AMS-Slots zugewiesen.
* **Finanz-Dashboard:** Reale Berechnung von Strom- und Materialkosten pro Druck. Neues Unified-Dashboard mit Preis/kg Auswertung.
* **Spulen-Logbuch:** Detaillierte Historie für jede einzelne Spule (Wann, wie viel, wie teuer).
* **In-App Handbuch:** Ein integriertes Mini-Wiki erklärt alle Features direkt im Programm.
* **System-Tray:** Die App kann nun minimiert im Hintergrund weiterlaufen.

---

## 🤝 Support & Spenden
VibeSpool ist ein Open-Source Hobbyprojekt. Wenn dir das Tool hilft, freue ich mich riesig über einen virtuellen Kaffee!

**Entwickelt von SirMetalizer | Mit speziellem Dank an Lena (Lead Inspiration & UX Design) & Kathi💡**
