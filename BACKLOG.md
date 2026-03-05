### 📋 Das VibeSpool Projekt-Backlog (Version 1.4+)

#### 🛒 1. ERP- & Material-Daten (Das kaufmännische Update)

* **Neue Datenfelder:** Jedes Filament bekommt Felder für **Lieferant**, **Artikelnummer (SKU)**, **Preis pro Rolle**, **Shop-Link** sowie **Drucktemperaturen** (Nozzle & Druckbett).
* **Einkaufsliste (Dashboard):** Eine eigene Übersichtsseite für alle Filamente, die auf "Nachbestellen" oder "Verbraucht" stehen.
* **Export-Funktion:** Diese Einkaufsliste mit einem Klick als Excel/CSV exportieren, um sie schnell beim Händler abzuarbeiten.

#### 📷 2. Scanner & QR-Code Features (NEU)

* **Lesbare QR-Codes (Fürs Handy):** Der generierte QR-Code enthält nicht mehr nur die reine ID, sondern einen für den Menschen lesbaren Satz (z. B. `ID: 1 | YUANEANG | PLA | Black/Red`).
* **Intelligentes Quick-ID-Feld:** Das Suchfeld in der App durchsucht gescannte Sätze automatisch (per Regex) nach der ID, damit Hardware-Handscanner am PC weiterhin problemlos funktionieren.
* **Webcam-Integration:** Ein Button in der App, der die PC-Webcam aktiviert, um den QR-Code direkt am Bildschirm scannen zu können (ohne Zusatz-Hardware).

#### 🧮 3. Tools & Rechner

* **Druckkosten-Rechner:** Ein eingebautes Tool. Man wählt eine Rolle aus dem Bestand, tippt die Gramm-Zahl und Druckzeit aus dem Slicer ein, und das Programm berechnet anhand des hinterlegten Rollen-Preises und eines Strompreises die exakten Druckkosten.

#### 🔄 4. Workflow & Handling

* **Spulen-Swap (AMS <-> Regal):** Ein "Tauschen"-Button. Wenn man eine Rolle aus dem Regal ins AMS legt und umgekehrt, tauschen die beiden Einträge per Klick ihre Lagerorte/Slots.

#### 📱 5. Plattformen & Mobile

* **Mobile Nutzung (Web-App):** Perspektivisch das Programm (z. B. mit Python Flask) als lokalen "Server" umbauen, damit man am Smartphone-Browser darauf zugreifen kann, während man vor dem Regal steht.

#### 🤖 6. Die "Industrie 4.0" Hardware-Vision

* **IoT Smart-Scale:** Schnittstelle für eine selbstgebaute WLAN-Waage mit Kamera (ESP32 + HX711). Rolle draufstellen -> QR-Code wird gescannt -> Gewicht wird erfasst -> VibeSpool aktualisiert das Bruttogewicht vollautomatisch im Hintergrund.
