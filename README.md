# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-1.9.7-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** VibeSpool ist ein leichtgewichtiges, lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle, mobile und kaufmännische Kontrolle über deine Spulen gibt.

<img width="1924" height="1044" alt="VibeSpool Main Dashboard" src="[https://github.com/user-attachments/assets/7234891c-0458-478b-8c5a-7d9e6cd184cb](https://github.com/user-attachments/assets/7234891c-0458-478b-8c5a-7d9e6cd184cb)" />

---

## ✨ Features

### 📱 NEU: Mobile Companion & Live-Dashboard
VibeSpool wird kabellos! Scanne einfach den QR-Code am Monitor und dein Handy wird zum **kabellosen Handyscanner**.
* **Keine App-Installation:** Läuft direkt im Browser über deinen lokalen Webserver.
* **Smart Foto-Scan:** Nutzt die native Kamera für blitzschnelle QR-Erkennung (Browser-kompatibel ohne HTTPS-Zertifikate).
* **Remote Control:** Buche Spulen am Regal um oder trage den Verbrauch am Handy ein – der PC synchronisiert sich in Echtzeit.

### 🏡 NEU: Home Assistant & MQTT Integration
Dein Lager wird Teil deines Smart Homes.
* **Live Broadcasting:** VibeSpool funkt den Bestand als JSON an deinen MQTT-Broker.
* **Automation Ready:** Erhalte Warnungen bei kritischen Füllständen oder visualisiere dein Filament-Gewicht auf deinem Home Assistant Dashboard.

### 🏷️ Label Creator & Smart PDF Export
Professionelle Etiketten inkl. QR-Code, Material-Icons und Drucktemperaturen.
* **NEU: PDF Smart Export:** Exportiere dein gesamtes Lager als PDF. Wähle zwischen **Rollendruckern** (1 Label pro Seite) oder **DIN-A4 Bögen** mit frei einstellbarem Gitter-Layout.

### 🤖 Bambu Lab AMS Live-Sync
Synchronisiere VibeSpool via MQTT mit deinem Bambu Lab Drucker. 
* Lese AMS-Slots aus und weise sie per Drag & Drop deinen Beständen zu.
* **One-Click Auto-Import:** Lege unbekannte Spulen im AMS sofort mit den korrekten Druckerdaten in VibeSpool an.

### 📦 Visuelles Regal- & Lagermanagement (Drag & Drop)
* **Doppeltiefe Regale:** Support für Schränke, in denen zwei Rollen hintereinander (Vorne/Hinten) lagern.
* **Kollisions-Schutz:** Warnt dich am PC und Handy, wenn ein Lagerplatz bereits belegt ist.
* **Drag & Drop:** Tausche Plätze intuitiv in der visuellen Übersicht aus oder verschiebe Spulen direkt ins Lager.

### 🎨 Smarte Multi-Color Render Engine
Erkennt Hex-Codes und Farbnamen automatisch. Trenne Farben mit `/` (z.B. `Rot / Gold`) und VibeSpool generiert dir die passende visuelle Vorschau (Dual/Tri-Color).

---

## 🚀 Installation & Start

### Für Nutzer (Windows)
1. Lade dir die neuste Version unter [Releases](https://github.com/SirMetalizer/VibeSpool/releases/latest) herunter.
2. Starte die **`VibeSpool_Win.exe`** – keine Installation von Python nötig!

### Für Entwickler
Stelle sicher, dass **Python 3.10+** installiert ist.

1. **Repository klonen:**
   ```bash
   git clone https://github.com/SirMetalizer/VibeSpool.git
   cd VibeSpool
   ```

2. **Abhängigkeiten installieren:**
   ```bash
   pip install Pillow pyzbar opencv-python qrcode paho-mqtt
   ```

3. **Starten:**
   ```bash
   python filament_gui.py
   ```

---

## 🆕 Was ist neu in Version 1.9.7? ("The Smart & Mobile Update")

* **Mobile Web-Interface:** Kabelloses Scannen und Bearbeiten via Smartphone.
* **MQTT-Broadcasting:** Nahtlose Anbindung an Home Assistant.
* **PDF-Batch-Export:** Erzeuge komplette Etiketten-Bögen für DIN-A4 oder Etikettendrucker.
* **Smarte Refill-Logik:** Auto-Auswahl der passenden Leerspule basierend auf dem Hersteller.
* **UI-Refactor:** Aufgeräumte Optionen; Hardware-Einstellungen wurden logisch in die Bereiche "Lager" und "Drucker" integriert.
* **Sicherheit:** Kollisionsprüfung verhindert Fehlbuchungen in belegte Regal-Slots.

---

## 🤝 Support & Spenden
VibeSpool ist ein Open-Source Hobbyprojekt, in das massiv viel Zeit und Herzblut geflossen ist. Wenn dir das Tool hilft, freue ich mich riesig über einen virtuellen Kaffee!

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://paypal.me/florianfranck)

---
**Entwickelt von SirMetalizer** | *Mit speziellem Dank an Lena (Lead Inspiration & UX Design)* 💡