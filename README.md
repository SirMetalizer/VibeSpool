# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-1.9.2-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** VibeSpool ist ein leichtgewichtiges, lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle und kaufmännische Kontrolle über deine Spulen gibt.

![VibeSpool Screenshot](https://metalizer.de/Vibespool.jpg)

---

## 🚀 NEU in v1.9.2: Das große "Customization & Workflow" Update

Dieses Update bringt das wohl meistgewünschte Feature für Neueinsteiger (den CSV-Import!), behebt die nervigsten Bugs und macht euren Workflow so schnell und anpassbar wie nie zuvor.

### ✨ Neue Features (Die Highlights)
* **📥 1-Klick CSV / Excel Import:** Keine Lust, 50 Spulen abzutippen? Importiere dein bestehendes Lager jetzt sekundenschnell aus einer Tabelle! VibeSpool erkennt die Spaltennamen automatisch. *(Eine Vorlage liegt direkt hier bei den Release-Dateien).*
* **🎨 Eigene Materialien & Farben:** Unter *⚙ Optionen -> 📋 Listen* könnt ihr ab sofort völlig frei eure eigenen Materialien (z.B. PAHT-CF) oder spezielle Farbbezeichnungen hinzufügen.
* **🏷️ Individuelle Regal-Fächer:** Nenne "Fach 1" ab sofort "Bambu PLA" oder "Kiste unterm Tisch". Klicke einfach auf das neue 🏷️-Icon neben der Slot-Auswahl. VibeSpool bucht bestehende Spulen im Hintergrund automatisch um!

### ⚡ Workflow & UI-Verbesserungen
* **🐑 "Klonen" & "Ins Lager" Buttons:** Blitzschnell Spulen duplizieren oder leere Fächer direkt ins Hauptlager verschieben.
* **🧮 Slicer-Verbrauch abziehen:** Trage einfach ein, was der Slicer berechnet hat, klicke auf "➖ Abziehen" und das Brutto-Gewicht aktualisiert sich sofort.
* **🧹 Aufgeräumte Dropdowns:** Spezial-Eigenschaften wie "Glow in Dark" oder "Transparent" wurden logisch in das Dropdown "Effekt / Typ" verschoben.
* **🖱️ Mausrad & Darkmode Upgrade:** Besser sichtbarer Scrollbalken im Darkmode und extrem robustes Scroll-Verhalten in der gesamten App.

### 🛠️ Kritische Bugfixes (Unter der Haube)
* **🛡️ Der "Item already exists" ID-Crash:** Das manuelle Vergeben von IDs führt nicht mehr zum Programmabsturz. Ein intelligenter Türsteher warnt jetzt bei doppelten IDs.
* **🧟‍♂️ Ghost-Fenster eliminiert:** VibeSpool beendet sich jetzt beim Klick auf das "X" absolut zuverlässig ohne im Hintergrund weiterzulaufen.
* **🚫 Der "tote" Speichern-Button:** Falsche Eingaben (z.B. Text in Zahlenfeldern) erzeugen jetzt eine saubere Fehlermeldung statt einfach stumm zu blockieren.

---

## 🌟 Weitere Highlights & Features

### 🤖 Bambu Lab AMS Live-Sync (Seit v1.9)
- **Live-Auslesen:** VibeSpool erkennt per Klick, welche Materialien und Farben gerade im AMS geladen sind.
- **Smart-Sync:** Weise den erkannten AMS-Slots mit wenigen Klicks deine Spulen aus dem Lager zu. VibeSpool bucht alte Spulen automatisch zurück ins Regal.
- **Lokal & Sicher:** Die Kommunikation läuft rein lokal über dein Heimnetzwerk (MQTT).

### 📦 Visuelles Lager & Management
* **Regal-Visualizer:** Erstelle dein eigenes Layout (z.B. 4 Reihen, 8 Slots). VibeSpool zeichnet dein Regal nach und zeigt dir exakt an, wo welche Spule liegt.
* **Klipper/Moonraker Sync:** Ziehe das verbrauchte Gewicht direkt von deinem Drucker ab. Wähle aus den letzten 10 Druckaufträgen exakt den passenden aus.
* **🔄 Quick-Swap Magie:** Tausche Spulen mit einem Klick zwischen Regal und dem AMS.

### 💰 Smart Financials (Kaufmännisches Dashboard)
* **Live-Wertberechnung:** VibeSpool berechnet bei jedem Wiegen im Hintergrund den auf den Cent genauen Restwert der Spule.
* **Finanz-Statistik:** Gesamtwert (in €) und Gewicht (in kg) deines Lagers auf einen Blick.

### 🛠️ Workflow & QoL (Quality of Life)
* **Webcam QR-Scan & RFID:** Schnelle Identifikation deiner Spulen via Kamera oder RFID-Reader.
* **Einkaufsliste & CSV-Export:** Markiere leere Spulen und exportiere deine Liste für Excel.
* **Flawless Dark/Light Mode:** Perfekt abgestimmte UI für jede Tageszeit.

---

## 🧵 Leerspulen-Datenbank & Gewichte

VibeSpool enthält eine integrierte Datenbank für Leerspulen-Gewichte, basierend auf dem großartigen Community-Spreadsheet.

### So nutzt du die Vorlagen:
1. Klicke in der Sidebar auf **"🧵 Leerspulen verwalten"**.
2. Klicke unten auf **"📋 Vorlagen"**.
3. Wähle deine Spule aus der Liste aus (z.B. "Bambu Lab (Reusable) (250g)") und klicke auf **"Übernehmen"**.
4. Klicke auf **"Neu anlegen"**, um sie dauerhaft in deine persönliche Liste zu übernehmen.

---

## 🛠️ Installation & Setup

VibeSpool benötigt keine komplizierten Datenbank-Server. Alle deine Daten liegen sicher in einer lokalen `inventory.json` Datei (auf Wunsch auch synchronisiert via OneDrive/Dropbox).

**Option A: Als Standalone `.exe` (Windows)**
1. Gehe zu den [Releases](https://github.com/SirMetalizer/VibeSpool/releases) hier auf GitHub.
2. Lade die neueste `VibeSpool_Win.exe` herunter.
3. Ausführen und loslegen! 

**Option B: Aus dem Source Code (Plattformunabhängig)**
1. Klone das Repository: `git clone https://github.com/SirMetalizer/VibeSpool.git`
2. Installiere die nötigen Pakete: `pip install Pillow qrcode paho-mqtt opencv-python pyzbar`
3. Starte das Tool: `python filament_gui.py`

*(Für die Einrichtung der Bambu Lab Integration schau bitte in die [BAMBU-INTEGRATION-HOWTO.md](BAMBU-INTEGRATION-HOWTO.md))*

---

## 🗺️ Roadmap (What's next?)

Wir haben große Pläne für die nächsten Versionen:
* **v2.0 - VibeSpool Remote:** Lokaler Webserver für eine smarte Tablet- und Smartphone-Ansicht in der Werkstatt.

---

## 🤝 Support & Spenden

VibeSpool ist ein Open-Source Hobbyprojekt, in das massiv viel Zeit, Liebe und Kaffee geflossen ist. 
Wenn dir das Tool deinen 3D-Druck-Alltag erleichtert, freue ich mich riesig über einen virtuellen Kaffee!

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://paypal.me/florianfranck)
---
**Entwickelt von SirMetalizer** | *Mit speziellem Dank an Lena (Lead Inspiration & UX Design)* 💡