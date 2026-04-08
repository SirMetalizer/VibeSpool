# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-1.9.8-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** VibeSpool ist ein leichtgewichtiges, lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle, mobile und kaufmännische Kontrolle über deine Spulen gibt.

<img width="1924" height="1044" alt="VibeSpool Main Dashboard" src="https://github.com/user-attachments/assets/7234891c-0458-478b-8c5a-7d9e6cd184cb" />

---

## ✨ Features

### 📊 NEU: Erweiterte Statistiken & Historie
Behalte deinen Verbrauch im Blick! VibeSpool loggt deinen Materialverbrauch im Hintergrund und visualisiert ihn in einem dynamischen 7-Tage-Balkendiagramm. Vertippt? Kein Problem, die neue Korrektur-Funktion rechnet das Gewicht sauber zurück.

### 🖱️ NEU: Workflow-Booster (Kontextmenüs)
* **Spalten-Konfigurator:** Rechtsklick auf den Tabellenkopf, um unnötige Spalten einfach auszublenden. Perfekt für kleine Monitore!
* **Quick-Actions:** Rechtsklick auf eine beliebige Spule für blitzschnelle Aktionen: Direkt ins AMS tauschen, Spule klonen, ausbuchen, Etikett drucken oder auf die Einkaufsliste setzen.

### 🛡️ NEU: Unzerstörbares MQTT (Offline-Buffer)
Dein Lager wird Teil deines Smart Homes. VibeSpool puffert alle Smart-Home-Updates (Home Assistant) lokal zwischen und feuert sie automatisch ab, sobald die Verbindung wiederhergestellt ist.

### 📱 Mobile Companion & Live-Dashboard
VibeSpool wird kabellos! Scanne einfach den QR-Code am Monitor und dein Handy wird zum **kabellosen Handyscanner**.
* **Keine App-Installation:** Läuft direkt im Browser über deinen lokalen Webserver.
* **Smart Foto-Scan:** Nutzt die native Kamera für blitzschnelle QR-Erkennung.
* **Remote Control:** Buche Spulen am Regal um oder trage den Verbrauch am Handy ein.

### 🤖 Bambu Lab AMS Live-Sync
Synchronisiere VibeSpool via MQTT mit deinem Bambu Lab Drucker.
* Lese AMS-Slots aus und weise sie per Drag & Drop deinen Beständen zu.
* **One-Click Auto-Import:** Lege unbekannte Spulen im AMS sofort in VibeSpool an.

---

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
Abhängigkeiten installieren:

Bash
pip install Pillow pyzbar opencv-python qrcode paho-mqtt
Starten:

Bash
python filament_gui.py
🆕 Was ist neu in Version 1.9.8? ("The Data & Workflow Update")
Spalten-Konfigurator: Individuelles Ein/Ausblenden der Haupttabelle.

Quick-Actions: Rechtsklick-Menü für rasend schnelle Spulen-Verwaltung.

Erweiterte Statistiken: Neues 7-Tage-Verbrauchs-Diagramm im Finanzen-Tab.

Fehlerkorrektur-System: "+" Button, um falsch eingetragenen Slicer-Verbrauch rückgängig zu machen.

MQTT Self-Healing: Offline-Buffer für zuverlässige Home-Assistant Übertragungen.

Branding: Neues, offizielles VibeSpool App-Icon.

🤝 Support & Spenden
VibeSpool ist ein Open-Source Hobbyprojekt. Wenn dir das Tool hilft, freue ich mich riesig über einen virtuellen Kaffee!

Entwickelt von SirMetalizer | Mit speziellem Dank an Lena (Lead Inspiration & UX Design) 💡