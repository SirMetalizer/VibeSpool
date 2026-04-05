# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-1.9.6-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** VibeSpool ist ein leichtgewichtiges, lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle und kaufmännische Kontrolle über deine Spulen gibt.

<img width="1924" height="1044" alt="image" src="https://github.com/user-attachments/assets/7234891c-0458-478b-8c5a-7d9e6cd184cb" />

<img width="913" height="444" alt="image" src="https://github.com/user-attachments/assets/50ab3ea3-a6af-47f0-b9bb-c1c97f0a8da8" />

***

# 🪶 VibeSpool – Das smarte Filament-Lager & AMS-Manager

**VibeSpool** ist eine mächtige, lokale Desktop-Anwendung zur Verwaltung deines 3D-Druck-Filaments. Egal ob du ein einzelnes Regal oder eine riesige Farm mit mehreren Bambu Lab AMS-Einheiten betreibst: VibeSpool behält den Überblick über deine Spulen, Restgewichte, Kosten und Lagerorte.

---

## ✨ Features

### 🏷️ Integrierter Label Creator
Generiere mit einem Klick wunderschöne, druckfertige Etiketten für deine Spulen! Der Label Creator erstellt PNG-Grafiken inkl. QR-Code (für den Schnell-Scan), Farb-Balken, Material und Drucktemperaturen. Perfekt für Dymo- oder Brother-Drucker.

### 🤖 Bambu Lab AMS Live-Sync
Synchronisiere VibeSpool in Echtzeit mit deinem Bambu Lab Drucker via MQTT. Lese die aktuell eingelegten Spulen aus, weise sie deinen Datenbank-Einträgen zu oder lege völlig neue Spulen mit der **"One-Click Auto-Import"** Funktion direkt aus den Druckerdaten an.

<img width="365" height="168" alt="image" src="https://github.com/user-attachments/assets/d2ed10d8-9121-4659-8bbd-be379774f0e1" />

### 🎨 Smarte Multi-Color Render Engine
VibeSpool generiert automatisch visuelle Icons für deine Spulen. 
* **Dual- & Tri-Color:** Trenne Farben mit einem `/` (z.B. `Rot / Schwarz / Gold`) und VibeSpool spaltet das Icon entsprechend auf.
* **Auto-Hex Engine:** Die Engine erkennt Hex-Codes automatisch und benennt sie anhand einer riesigen internen Datenbank (z.B. `#50C878` wird sofort zu *Smaragdgrün*).

### 📦 Visuelles Regal- & Lagermanagement (Drag & Drop)
Plane dein Lager digital! Erstelle Regale mit eigenen Reihen und Spalten. 
* **Doppeltiefe Regale:** Verstaust du zwei Spulen hintereinander? Aktiviere den (V) Vorne / (H) Hinten Modus!
* **Drag & Drop:** Tausche Spulenplätze oder wirf sie per Maus direkt in die Lager-Kiste.
* **Isolierte Benennung:** Gib Fächern individuelle Namen (z.B. "Fach 1 - PLA").

<img width="653" height="884" alt="image" src="https://github.com/user-attachments/assets/f334a92e-8083-4817-961c-1426977cb03a" />

### 💰 Finanz-Dashboard & Einkaufsliste
Behalte deine Kosten im Griff. VibeSpool berechnet den exakten Restwert deiner Spulen basierend auf dem Netto-Gewicht. Leere oder markierte Spulen landen automatisch auf einer exportierbaren Einkaufsliste (inkl. Shop-Links).

<img width="607" height="312" alt="image" src="https://github.com/user-attachments/assets/9f406fa4-d7e2-4228-a4b9-5a7eff46fbb4" />

### 🔄 Moonraker / Klipper Sync
Verbinde VibeSpool mit deinem Klipper-Drucker. Ziehe den Filament-Verbrauch des letzten Drucks mit nur einem Klick direkt vom Brutto-Gewicht der aktiven Spule ab.

### 📱 QR-Code & RFID Unterstützung
Generiere QR-Codes für deine Spulen oder nutze einen RFID-Reader. Ein kurzer Scan über die Webcam oder den Reader reicht, um die Spule sofort in VibeSpool aufzurufen.

---

## 🚀 Installation & Start

VibeSpool ist in Python geschrieben und nutzt `Tkinter` für die grafische Oberfläche.

### Voraussetzungen
Lade dir die neuste Version unter [https://github.com/SirMetalizer/VibeSpool/releases/latest](https://github.com/SirMetalizer/VibeSpool/releases/latest) runter. 
Aktueller Support: Windows.

### Für Entwickler
Stelle sicher, dass **Python 3.x** auf deinem System installiert ist.

### 1. Repository klonen
```bash
git clone [https://github.com/SirMetalizer/VibeSpool.git](https://github.com/SirMetalizer/VibeSpool.git)
cd VibeSpool
```

### 2. Abhängigkeiten installieren
Für die Kamera-Scans, Bildverarbeitung und MQTT-Anbindung werden folgende Pakete benötigt:
```bash
pip install Pillow pyzbar opencv-python qrcode paho-mqtt
```

### 3. VibeSpool starten
Führe einfach die Hauptdatei aus:
```bash
python filament_gui.py
```

---

## 🆕 Was ist neu in Version 1.9.6?

Das **"Label & Deep Storage"** Update bringt massive Workflow-Boosts:
* **Label Creator:** Drucke eigene Etiketten direkt aus VibeSpool!
* **Doppeltiefe Regale:** Verstaue virtuell zwei Rollen hintereinander (Vorne/Hinten).
* **Drag & Drop Swaps:** Tausche Spulenplätze in der Regalansicht intuitiv per Mauszeiger.
* **Smart Color-Picker:** Vollständige Überarbeitung der Farbeingabe mit Auto-Ausfüllen von Namen und Hex-Codes.
* **Regal-Rettungsprotokoll:** Gelöschte Regale werfen darin liegende Spulen nun sicher in das allgemeine "LAGER".
* **Live-Table Sort:** Das AMS bleibt in der Tabelle nun absolut priorisiert immer oben angeheftet, egal wie umgebucht wird.

<img width="373" height="946" alt="image" src="https://github.com/user-attachments/assets/98504c33-81c6-4d24-b86d-b782d19c5b6f" />
<img width="763" height="554" alt="image" src="https://github.com/user-attachments/assets/cbae14fb-74cb-47a3-895f-f5b4ece63de6" />

---

## 🛠️ Daten & Backups
Alle deine Spulen, Einstellungen und Presets werden lokal als `.json` Dateien gespeichert. Du kannst den Speicherpfad unter `Optionen -> System` jederzeit einsehen oder ändern. VibeSpool bietet zudem eine integrierte Backup-Funktion, um deine Datenbank als ZIP-Datei zu exportieren.

---

## 🤝 Support & Spenden
VibeSpool ist ein Open-Source Hobbyprojekt, in das massiv viel Zeit, Liebe und Kaffee geflossen ist. 
Wenn dir das Tool deinen 3D-Druck-Alltag erleichtert, freue ich mich riesig über einen virtuellen Kaffee!

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://paypal.me/florianfranck)
---
**Entwickelt von SirMetalizer** | *Mit speziellem Dank an Lena (Lead Inspiration & UX Design)* 💡