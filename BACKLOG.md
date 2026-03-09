## 📋 VibeSpool Master-Backlog (v1.6 - v2.0)

### 🚀 Prio 1: Das "Wartungs- & Update" Paket (v1.6)

* **GitHub-Update-Motor:** Reaktivierung der automatischen Abfrage der neuesten Version.
* **Update-Button:** Manueller Check in den Settings.
* **In-App Updater:** Automatischer Download und Austausch der `.exe`.
* **Fixes:** Fenster-Skalierung bei extrem langen Pfaden (OneDrive-Bug).

### 📡 Prio 2: Der "Universal-Identifikations" Hub (v1.7)

* **Hybrid-Modus (RFID & Quick-ID):** * Umschalter in den Settings: "RFID-Modus" vs. "Manueller Modus".
* Im RFID-Modus wird das Quick-ID Feld für Tastatur-Eingaben gesperrt und wartet rein auf den "Input" des Readers.


* **RFID-Tag-Kopplung:** Neues Feld im Bearbeitungs-Menü, um eine eindeutige RFID-Seriennummer fest mit einer Spule zu verknüpfen.
* **QR-Code Scan via Webcam:** Integration einer einfachen Kamera-Bibliothek (z.B. `opencv`), um QR-Codes direkt am PC zu scannen, falls kein RFID vorhanden ist.

### 🌐 Prio 3: Connectivity & Standards (v1.8)

* **Spoolman / OpenSpool API:** Synchronisation deiner lokalen Datenbank mit dem Open-Source Standard für 3D-Drucker.
* **Klipper/Moonraker Integration:** Automatisches Abziehen des Gewichts nach einem beendeten Druckauftrag via API-Abfrage.

### 📱 Prio 4: Mobile & Web (v1.9)

* **VibeSpool Remote:** Kleiner lokaler Webserver (Flask), um den Bestand auf dem Handy im WLAN anzuzeigen.
* **Touch-Optimierung:** Eine spezielle Ansicht für Tablets im Werkstatt-Modus.

### 💰 Prio 5: Smart Financials (v2.0)

* **Druckkosten-Rechner:** Preis pro Gramm Berechnung basierend auf den v1.5 Kaufdaten.
* **Bestands-Statistik:** Grafische Auswertung: Welches Material drucke ich am meisten? Wie viel Geld liegt gerade in meinem Regal?
