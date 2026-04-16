# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-1.10.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** VibeSpool ist ein lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle, mobile und kaufmännische Kontrolle über deine Spulen gibt.

<img width="1924" height="1044" alt="VibeSpool Main Dashboard" src="https://github.com/user-attachments/assets/7234891c-0458-478b-8c5a-7d9e6cd184cb" />

---

## ✨ Features

### ☁️ Bambu Cloud API & Smart-Match
Verbinde VibeSpool mit der Bambu Cloud. Das System lädt deine fertigen Druckaufträge herunter, erkennt automatisch, welche Spulen im AMS verwendet wurden (**Smart-Match**) und teilt den Verbrauch bei Multi-Color-Drucken grammgenau auf.

<img width="1014" height="805" alt="image" src="https://github.com/user-attachments/assets/aa1822b7-382e-4503-b4f0-0906a73616a3" />

### 💰 Druckkosten-Rechner & Logbuch
VibeSpool kombiniert den Kaufpreis deiner Spulen mit deinem lokalen Strompreis und der Laufzeit des Drucks. Bei jedem Cloud-Sync siehst du auf den Cent genau, was dein Druck gekostet hat. Alles wird im **Spulen-Logbuch** dauerhaft als "Kontoauszug" gespeichert.

### 📊 Unified Analytics Dashboard
Ein interaktives Dashboard zeigt dir den genauen Bestandswert deines Lagers, den durchschnittlichen Preis pro Kilogramm für jedes Material und einen 7-Tage-Verbrauchsverlauf als Balkendiagramm.

### 📥 System-Tray & Hintergrund-Monitor
Schließe das Fenster und VibeSpool läuft lautlos im Windows-Tray (neben der Uhr) weiter. Es lauscht im Hintergrund auf deinen Drucker und meldet sich über smarte **Toast-Benachrichtigungen**, sobald ein Druck verrechnet wurde.

### 📱 Mobile Companion & Handyscanner
VibeSpool wird kabellos! Scanne einfach den QR-Code am Monitor und dein Handy wird zum **kabellosen Handyscanner**.
* **Keine App-Installation:** Läuft direkt im Browser über deinen lokalen Webserver.
* **Hersteller-Barcodes:** Scanne Strichcodes von Originalverpackungen – VibeSpool lernt die Marken automatisch!

### ⚖️ Die Schlaue Waage
Nie wieder Leergewichte raten. Trage das Brutto-Gewicht ein, das deine Küchenwaage anzeigt. VibeSpool erkennt Hersteller und Material, zieht das korrekte Leerspulen-Gewicht ab und bucht das Netto-Gewicht ein.

### 📦 Lagerverwaltung & Doppeltiefe Regale
Bilde dein echtes Regal virtuell nach (z.B. 4 Reihen, 8 Spalten). VibeSpool unterstützt sogar **doppeltiefe Regale** (2 Spulen hintereinander) und bietet eine **Quick-Swap** Funktion, um Spulen blitzschnell ins AMS zu tauschen.

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

## 🆕 Was ist neu in Version 1.10.0? ("The Smart Pro Update")
Bambu Cloud & Smart-Match: Abzüge aus der Cloud werden jetzt vollautomatisch den richtigen AMS-Slots zugewiesen.

* **Finanz-Dashboard**: Reale Berechnung von Strom- und Materialkosten pro Druck. Neues Unified-Dashboard mit Preis/kg Auswertung.

* **Spulen-Logbuch**: Detaillierte Historie für jede einzelne Spule (Wann, wie viel, wie teuer).

* **In-App Handbuch**: Ein integriertes Mini-Wiki erklärt alle Features direkt im Programm.

* **System-Tray**: Die App kann nun minimiert im Hintergrund weiterlaufen.

## 🤝 Support & Spenden
VibeSpool ist ein Open-Source Hobbyprojekt. Wenn dir das Tool hilft, freue ich mich riesig über einen virtuellen Kaffee!

**Entwickelt von SirMetalizer | Mit speziellem Dank an Lena (Lead Inspiration & UX Design) & Kathi💡**