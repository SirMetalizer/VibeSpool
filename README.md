# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-1.7-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** Schluss mit dem *"Wie viel ist da noch drauf?"*-Raten und dem Excel-Chaos in der Werkstatt. VibeSpool ist ein leichtgewichtiges, lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle und kaufmännische Kontrolle über deine Spulen gibt.

![VibeSpool Screenshot](https://metalizer.de/Vibespool.jpg)

---

## ✨ Features (v1.7)

### 📦 Visuelles Lager & AMS Management
* **Regal-Visualizer:** Erstelle dein eigenes Layout (z.B. 4 Reihen, 8 Slots). VibeSpool zeichnet dein Regal nach und zeigt dir exakt an, wo welche Spule liegt. XXL-Regale werden dank dynamischem Scrollen problemlos unterstützt.
* **🔄 Quick-Swap Magie:** Tausche Spulen mit einem Klick zwischen Regal und dem Bambu Lab AMS. Das Tool merkt sich den alten Platz und räumt die ausgewechselte Spule virtuell exakt dorthin zurück.

### 💰 Smart Financials (Kaufmännisches Dashboard)
* **Live-Wertberechnung:** Trage den Kaufpreis und die Kapazität ein. VibeSpool berechnet bei jedem Wiegen im Hintergrund den auf den Cent genauen Restwert der Spule.
* **Finanz-Statistik:** Ein Klick und du siehst den Gesamtwert (in €) und das Gesamtgewicht (in kg) deines gesamten Lagers, aufgeschlüsselt nach Materialien.

### 🛠️ Workflow & QoL (Quality of Life)
* **QR-Codes:** Generiere auf Knopfdruck QR-Codes für deine Spulen zur schnellen Identifikation.
* **Einkaufsliste & CSV-Export:** Markiere leere oder fast leere Spulen für die Einkaufsliste und exportiere sie für Excel.
* **Auto-Updater:** VibeSpool checkt (sanft und unaufdringlich) über die GitHub-API, ob eine neue Version verfügbar ist.
* **Flawless Dark/Light Mode:** Perfekt abgestimmte UI, egal ob du nachts oder tagsüber druckst.

---

## 🚀 Installation & Start

VibeSpool benötigt keine komplizierten Datenbank-Server. Alle deine Daten liegen sicher in einer lokalen `inventory.json` Datei (auf Wunsch auch synchronisiert via OneDrive/Dropbox).

**Option A: Als Standalone `.exe` (Windows)**
1. Gehe zu den [Releases](https://github.com/SirMetalizer/VibeSpool/releases) hier auf GitHub.
2. Lade die neueste `VibeSpool_Win.exe` herunter.
3. Ausführen und loslegen! 

**Option B: Aus dem Source Code (Plattformunabhängig)**
1. Klone das Repository: `git clone https://github.com/SirMetalizer/VibeSpool.git`
2. Installiere die nötigen Pakete: `pip install Pillow qrcode`
3. Starte das Tool: `python filament_gui.py`

---

## 🗺️ Roadmap (What's next?)

Wir haben große Pläne für die nächsten Versionen:
* **v1.8 - Hardware Hub:** Direkte Integration von USB-RFID-Readern und Webcam-QR-Scannern.
* **v1.9 - API Connectivity:** Anbindung an Spoolman/OpenSpool und Klipper/Moonraker zum automatischen Abziehen des verbrauchten Gewichts nach dem Druck.
* **v2.0 - VibeSpool Remote:** Lokaler Webserver für eine smarte Tablet- und Smartphone-Ansicht in der Werkstatt.

---

## 🤝 Support & Spenden

VibeSpool ist ein Open-Source Hobbyprojekt, in das massiv viel Zeit, Liebe und Kaffee geflossen ist. 
Wenn dir das Tool deinen 3D-Druck-Alltag erleichtert, freue ich mich riesig über einen virtuellen Kaffee!

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://paypal.me/florianfranck)
---
**Entwickelt von SirMetalizer** | *Mit speziellem Dank an Lena (Lead Inspiration & UX Design)* 💡