### 🛠️ 1. Die großen Sidebar-Werkzeuge (Das Herzstück)
* **📦 Regal-Visualisierer:** Die grafische Ansicht deiner Regale und AMS-Einheiten (wo man sieht, welches Fach voll oder leer ist).
* **🏷️ Label-Drucker:** Der QR-Code- und Etiketten-Generator für deine Spulen.
* **📊 Finanz-Dashboard:** Das große Statistik-Center mit dem Balkendiagramm, Durchschnittspreis pro kg und dem Kostenschnellrechner.
* **☁️ Bambu Cloud-Sync:** Der Abruf der letzten Drucke inkl. Smart-Match (Zeitmaschine) und dem "Abziehen"-Formular.
* **📝 Auftrags-Planer (Print Queue):** Das MES-System für geplante Druckaufträge inkl. Links und Zuweisungen.

### 🖱️ 2. Tabellen- & Listen-Komfort
* **🔍 Suche & Filter:** Die Suchleiste und die Dropdowns oben (Material, Ort) sind aktuell noch Dummys. Sie müssen wieder mit der Tabelle verbunden werden.
* **⚡ Quick-Action Menü (Rechtsklick):** Das praktische Menü beim Rechtsklick auf eine Spule (Schnell ins AMS schieben, Klonen, Leer melden).
* **↕️ Sortierung:** Die Tabelle muss wieder klickbare Spaltenköpfe bekommen, damit man z.B. nach "Rest(g)" sortieren kann.
* **📖 Spulen-Logbuch:** Der "Kontoauszug" für jede einzelne Spule, der zeigt, wann wie viel abgezogen wurde.

### ⚙️ 3. Einstellungen & System-Anbindung
* **⚙️ Optionen-Menü:** Das komplette Einstellungs-Panel (Pfade, Preise, API-Keys, Regal-Konfiguration).
* **🌐 Mobile Scanner Server:** Der Hintergrund-Webserver, damit dein Handy sich mit VibeSpool verbinden und QR-Codes scannen kann.
* **📡 MQTT & Live-Sync:** Die Hintergrund-Verbindung zum Bambu-Drucker (für die Slot-Erkennung) und Home Assistant.
* **📥 System-Tray:** Das Minimieren der App in die Windows-Taskleiste (neben die Uhr), damit sie unsichtbar im Hintergrund weiterläuft.
* **💾 Backup & Export:** Die Funktion, um alle Daten als `.zip` oder Excel (`.csv`) zu exportieren.

---

### 🗺️ Wie gehen wir vor?

Das sieht nach viel aus, aber da wir die Logik (`data_manager.py`, `utils.py` etc.) nicht verändern müssen, ist das reine "Design-Arbeit". Das geht extrem schnell!

Mein Vorschlag für die logische Reihenfolge:
1. **Such- & Filterleiste aktivieren** + **Rechtsklick-Menü** (Damit die Haupttabelle 100% fertig ist).
2. Das **⚙️ Optionen-Menü** (Das brauchen wir, weil dort die Preise für die Finanz-Tools stehen).
3. Danach suchen wir uns die großen Tools aus (Regale, Cloud, Aufträge).

Sollen wir direkt mit **Schritt 1 (Suche, Filter & Rechtsklick-Menü)** weitermachen? Das ist in 5 Minuten erledigt! 😎