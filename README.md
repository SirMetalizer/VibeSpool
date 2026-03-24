# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-1.8-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** VibeSpool ist ein leichtgewichtiges, lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle und kaufmännische Kontrolle über deine Spulen gibt.

![VibeSpool Screenshot](https://metalizer.de/Vibespool.jpg)

---

## 🚀 NEU in v1.8: Der "Connectivity & Workflow" Hub

Dieses Update macht VibeSpool intelligenter, kommunikativer und deutlich komfortabler!

*   **🤖 Klipper/Moonraker Sync:** Ziehe das verbrauchte Gewicht direkt von deinem Drucker ab. Wähle aus den letzten 10 Druckaufträgen exakt den passenden aus.
*   **🧵 Leerspulen-Presets:** Über 40 Marken-Vorlagen (Bambu Lab, Prusa, etc.) mit hinterlegten Gewichten für den Blitz-Import.
*   **⚙️ UX-Boost:** Neues Tab-basiertes Einstellungsmenü und ein smartes Optionen-Dropdown für schnellen Zugriff.
*   **🛠️ Local-First:** Automatische Erkennung deiner Daten im Programmordner oder Dokumente-Verzeichnis.

---

## ✨ Features (v1.8)

### 📦 Visuelles Lager & AMS Management
* **Regal-Visualizer:** Erstelle dein eigenes Layout (z.B. 4 Reihen, 8 Slots). VibeSpool zeichnet dein Regal nach und zeigt dir exakt an, wo welche Spule liegt.
* **🤖 Drucker-Historie:** Direkte Anbindung an Klipper (Moonraker API), um Filamentverbräuche ohne Nachwiegen zu übernehmen.
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

VibeSpool enthält eine integrierte Datenbank für Leerspulen-Gewichte, basierend auf dem großartigen Community-Spreadsheet:
👉 [Unofficial Filament Spool Compatibility Spreadsheet](https://docs.google.com/spreadsheets/d/1LGVjAbGjvIjvOFQsDi8lSK9-vy7GfGhgVP41sNffh6I/edit?gid=1679778390#gid=1679778390)

### So nutzt du die Vorlagen:
1. Klicke in der Sidebar auf **"🧵 Leerspulen verwalten"**.
2. Klicke unten auf **"📋 Vorlagen"**.
3. Wähle deine Spule aus der Liste aus (z.B. "Bambu Lab (Reusable) (250g)") und klicke auf **"Übernehmen"**.
4. Klicke auf **"Neu anlegen"**, um sie dauerhaft in deine persönliche Liste zu übernehmen.

---

## 🛠️ Installation & Start

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