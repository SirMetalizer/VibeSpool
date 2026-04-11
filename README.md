# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-1.9.9-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** VibeSpool ist ein leichtgewichtiges, lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle, mobile und kaufmännische Kontrolle über deine Spulen gibt.

<img width="1924" height="1044" alt="VibeSpool Main Dashboard" src="https://github.com/user-attachments/assets/7234891c-0458-478b-8c5a-7d9e6cd184cb" />

---

## ✨ Features

### 🔍 NEU: Omni-Search & Notizen
Finde Spulen blitzschnell! Die neue globale Suche durchkämmt nicht nur Namen und Farben, sondern auch SKUs, Lieferanten, URLs und deine persönlichen Notizen. Tippe einfach "Amazon Rot" oder "12345" und VibeSpool filtert das Lager in Echtzeit.

### 🌙 NEU: Native Windows 11 Dark Mode
Schluss mit grellen Rändern! VibeSpool zwingt nun auch die native Windows-Titelleiste (inklusive Minimieren/Schließen-Buttons) in einen eleganten Dark Mode. 

### 📊 Erweiterte Statistiken & Historie
Behalte deinen Verbrauch im Blick! VibeSpool loggt deinen Materialverbrauch im Hintergrund und visualisiert ihn in einem dynamischen 7-Tage-Balkendiagramm. Vertippt? Kein Problem, die Korrektur-Funktion rechnet das Gewicht sauber zurück.

### 🖱️ Workflow-Booster (Kontextmenüs)
* **Spalten-Konfigurator:** Rechtsklick auf den Tabellenkopf, um unnötige Spalten einfach auszublenden.
* **Quick-Actions:** Rechtsklick auf eine beliebige Spule für blitzschnelle Aktionen: Direkt ins AMS tauschen, Spule klonen, ausbuchen oder Etikett drucken.

### 🛡️ Unzerstörbares MQTT (Offline-Buffer)
Dein Lager wird Teil deines Smart Homes. VibeSpool puffert alle Smart-Home-Updates (Home Assistant) lokal zwischen und feuert sie automatisch ab, sobald die Verbindung wiederhergestellt ist.

### 📱 Mobile Companion & Live-Dashboard
VibeSpool wird kabellos! Scanne einfach den QR-Code am Monitor und dein Handy wird zum **kabellosen Handyscanner**.
* **Keine App-Installation:** Läuft direkt im Browser über deinen lokalen Webserver.
* **Remote Control:** Buche Spulen am Regal um oder trage den Verbrauch am Handy ein.

### 🤖 Bambu Lab AMS Live-Sync
Synchronisiere VibeSpool via MQTT mit deinem Bambu Lab Drucker. Lese AMS-Slots aus, weise sie per Drag & Drop deinen Beständen zu und importiere unbekannte Spulen mit einem Klick.

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

## 🆕 Was ist neu in Version 1.9.9? ("The Search & Polish Update")

* **Omni-Search:** Aggressive, globale Textsuche über alle Felder (inkl. Multi-Word-Support).
* **Kaufmännisches Notizfeld:** Neues Eingabefeld für Spulen-spezifische Kommentare.
* **Native Dark Mode:** Die Windows-Titelleiste passt sich nun dem dunklen Theme an.
* **Sortier-Gedächtnis:** VibeSpool merkt sich nun die letzte Sortierung über Neustarts hinweg.
* **Smart Refill Logic:** Leere Spulen setzen das Bruttogewicht nun 100% zuverlässig auf 0g.
* **Amazon Affiliate Support:** Shop-Links zu Amazon unterstützen nun den Entwickler (deaktivierbar in den Einstellungen).

---

## 🤝 Support & Spenden
VibeSpool ist ein Open-Source Hobbyprojekt. Wenn dir das Tool hilft, freue ich mich riesig über einen virtuellen Kaffee!

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://paypal.me/florianfranck)

---
**Entwickelt von SirMetalizer** | *Mit speziellem Dank an Lena (Lead Inspiration & UX Design)* 💡