# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** VibeSpool ist ein lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle, mobile und kaufmännische Kontrolle über deine Spulen gibt.

<img width="1924" height="1044" alt="VibeSpool Main Dashboard" src="https://github.com/user-attachments/assets/7234891c-0458-478b-8c5a-7d9e6cd184cb" />

---

## 🆕 Was ist neu in Version 2.1.0? ("The Finance, Archive & Scroll Update")
Dieses Update bringt großartige neue Features für Analysen, Auftrags-Management und eine noch reibungslosere Bedienung!

### ✨ Die Highlights:

* **📊 Finanzen nach Hersteller & Farbe:** Im Analytics-Dashboard gibt es ein neues Register für die detaillierte Aufteilung nach Marke (Hersteller) und bereinigter Farbe. Sämtliche Tabellenspalten im Dashboard lassen sich jetzt per Klick interaktiv sortieren!
* **📝 Auftrags-Planer V2 (Archiv & Bilder):** Druckaufträge sind nun in eine aktive "Warteschlange" und ein "Archiv" für abgeschlossene Aufträge aufgeteilt. Du kannst Modellbilder hochladen (die automatisch ressourcenschonend komprimiert werden) und siehst diese direkt als Vorschau. Beim Abschließen werden Kosten und Verbrauch automatisch in das Spulen-Logbuch übernommen.
* **📜 Logbuch-Editor mit Preiskalkulatoren:** Einträge im Spulen-Logbuch können jetzt per Doppelklick editiert werden. Ein integrierter Rechner ermittelt dabei automatisch Materialkosten und Verkaufspreise basierend auf deiner gewünschten Gewinnmarge.
* **📦 Responsive Auto-Scroll:** Beim Drag & Drop von Spulen in der Regal- oder AMS-Ansicht scrollt das Fenster nun vollautomatisch mit, wenn du dich dem Fensterrand näherst. Perfekt für große Lager oder kleinere Monitore.

---

## 📋 Features im Überblick

Hier ist eine Zusammenfassung aller Kernfunktionen von VibeSpool:

* **🎨 Modernes "Apple-Look" Interface:** Clean & responsive GUI im "Apple-Design" (optimiert für Light- und Darkmode).
* **📦 Visuelle Lagerverwaltung:** Virtuelles Abbild deiner Regale (inkl. Doppeltiefe & Quick-Swap ins AMS) und responsivem Drag & Drop Auto-Scroll.
* **☁️ Bambu Cloud Sync & Smart-Match:** Vollautomatisches Synchronisieren deiner Druckaufträge und grammgenauer Materialabzug inkl. historischem AMS-Gedächtnis.
* **🤖 Bambu AMS Live-Sync via MQTT:** Echtzeitabgleich der AMS-Slots im lokalen Netzwerk.
* **📝 MES Auftrags-Planer:** Verwalten von Kunden, Projekten, Notizen, Modell-Links und -bildern inkl. Archiv und automatisierter Preiskalkulation beim Beenden.
* **💰 Integriertes Cost Center:** Globale Berechnung von Material- und Stromkosten sowie Maschinenverschleiß und Wunsch-Gewinnmarge.
* **🧮 Standalone-Kostenrechner:** Schnelle Preiskalkulation für Kundenangebote.
* **📜 Editierbares Spulen-Logbuch:** Lückenloser Kontoauszug für jede Spule mit nachträglicher Editierfunktion (Auto-Heal).
* **⚖️ Die Schlaue Waage:** Automatische Netto-Gewichtsberechnung anhand von vordefinierten Leerspulen-Gewichten bekannter Marken.
* **📱 Mobile Companion & Barcodescanner:** Kabellose Steuerung und Einscannen von Filament-Barcodes direkt über das eigene Smartphone.
* **🏷️ Label Creator & QR-Code-Generator:** Etikettendruck für Spulen auf DIN A4 PDF-Bögen oder Rollen-Etikettierern.
* **🛒 Einkaufsliste / Nachbestell-Manager:** Übersicht leerer Filamente mit direkten Shop-Links (Bambu, Amazon etc.) und CSV-Export.
* **🧪 Flow- & K-Wert-Rechner:** Schnelle Kalibrierung der Flussrate direkt in der App.
* **🔐 OAuth2 Login & Sicherheit:** Sichere Anmeldung bei MakerWorld direkt über deinen Webbrowser (ohne manuelle Passworteingabe).
* **📥 System-Tray & Hintergrundbetrieb:** Lautlose Ausführung im Windows-System-Tray mit Toast-Benachrichtigungen bei fertigen Drucken.
* **📤 Backup & Restore:** Einfacher Daten-Export und -Import als ZIP-Archiv.
* **📋 CSV-Import:** Bequeme Migration von Spulendaten aus alten Tabellen.
* **📚 In-App Handbuch:** Integriertes Wiki zur Erklärung aller Programmfunktionen.

---

## ✨ Weitere Features (Detail-Ansicht)

### ☁️ Bambu Cloud API & Smart-Match
Verbinde VibeSpool mit der Bambu Cloud. Das System lädt deine fertigen Druckaufträge herunter, erkennt automatisch, welche Spulen im AMS verwendet wurden (**Smart-Match**) und teilt den Verbrauch bei Multi-Color-Drucken grammgenau auf.

<img width="1014" height="805" alt="image" src="https://github.com/user-attachments/assets/aa1822b7-382e-4503-b4f0-0906a73616a3" />

### 📝 NEU: Auftrags-Planer (Print Queue & MES):
VibeSpool wird zur Schaltzentrale deiner Druck-Aufträge! Mit dem neuen Planungs-Tool kannst du anstehende Drucke verwalten. Weise Kunden oder Projekt-Titel zu, speichere direkte Links zu den 3D-Modellen und hinterlege genaue Notizen (z.B. "Marble für Body, Grün für Schrift").

**Das Highlight:** Du kannst die exakten Spulen aus deinem Inventar (inkl. Multi-Color ID 1 + ID 2) direkt dem Auftrag zuweisen! In Version 2.1.0 erweitert um ein Archiv für abgeschlossene Aufträge, Bild-Uploads für Modelle und automatisierte Preiskalkulation beim Fertigstellen.

<img width="1068" height="747" alt="image" src="https://github.com/user-attachments/assets/720140a3-a733-4e17-bfdd-0f3322211ff3" />

### 💰 Das Cost Center (Gewerbe-Kalkulation)
VibeSpool berechnet nicht nur Material- und Stromkosten, sondern berücksichtigt auch Maschinenverschleiß (pro Druckstunde) und schlägt automatisch deine Gewinnmarge (%) auf. Alle Drucke über alle Spulen hinweg laufen im globalen Kassenbuch zusammen. Ein Standalone Quick-Cost Rechner hilft dir bei schnellen Kundenangeboten.

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


## 🚀 Installation & Start

### Für Nutzer (Windows & Mac)
1. Lade dir die neuste Version unter [Releases](https://github.com/SirMetalizer/VibeSpool/releases/latest) herunter.
2. Starte die **`VibeSpool_Win.exe`** (oder `.app` auf dem Mac) – keine Installation von Python nötig!

### Für Entwickler
Stelle sicher, dass **Python 3.10+** installiert ist.

1. **Repository klonen:**

  ```bash
git clone [https://github.com/SirMetalizer/VibeSpool.git](https://github.com/SirMetalizer/VibeSpool.git)
cd VibeSpool
   ```

Abhängigkeiten installieren:

   ```bash
pip install Pillow pyzbar opencv-python qrcode paho-mqtt pystray requests
   ```
Starten:

   ```bash
python filament_gui.py
   ```

## 🆕 Was ist neu in Version 2.0.3? ("The Time Machine & Security Update")
* **🔐 Sicherer Browser-Login (OAuth2):** Vollautomatischer Login-Flow für MakerWorld/BambuLab via Webbrowser.
* **🕰️ Smart AMS Memory:** Hintergrund-Snapshots der AMS-Belegung zur korrekten historischen Zuordnung bei Cloud-Drucken.
* **📦 Setup-Installer:** Professionelles Windows-Installationsprogramm für bequemen Desktop- und Startmenü-Zugriff.
* **🌈 Rainbow-Icon:** Regenbogen-Filamente erhalten automatisch farbenfrohe Icons.

## 🆕 Was ist neu in Version 1.10.0? ("The Smart Pro Update")
* **Finanz-Dashboard**: Reale Berechnung von Strom- und Materialkosten pro Druck. Neues Unified-Dashboard mit Preis/kg Auswertung.
* **Spulen-Logbuch**: Detaillierte Historie für jede einzelne Spule (Wann, wie viel, wie teuer).
* **In-App Handbuch**: Ein integriertes Mini-Wiki erklärt alle Features direkt im Programm.
* **System-Tray**: Die App kann nun minimiert im Hintergrund weiterlaufen.

## 🤝 Support & Spenden
VibeSpool ist ein Open-Source Hobbyprojekt. Wenn dir das Tool hilft, freue ich mich riesig über einen virtuellen Kaffee!

**Entwickelt von SirMetalizer | Mit speziellem Dank an Lena (Lead Inspiration & UX Design) & Kathi💡**
