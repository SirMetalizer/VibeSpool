# 🚀 Release: VibeSpool v2.5.0 – Auftragsplaner & Projektverlauf Pro Update

Mit der Version **v2.5.0** erhält VibeSpool ein umfassendes Upgrade für den **Auftragsplaner (Print Queue)** und die **Projektverwaltung**! Von erweiterten Freitextfeldern über dynamische Stückzahl-Berechnung bis hin zu echten Verkaufspreisen, Gewinnspannen und interaktiven Modellbildern mit Zoom.

---

## ✨ Die Highlights dieser Version

### 1. 🖼️ Modellbilder: Zoom, Vergrößerung & System-Viewer
* **Bildvorschau vergrößert:** Das Vorschaubild im Auftragsplaner und im Projektverlauf wurde vergrößert (bis 240px Breite).
* **Interaktiver Bildbetrachter (`JobImageViewerDialog`):** Ein Klick auf das Bild öffnet das Modell in einem modalen Viewer mit **Zoom (+ / - / 1:1)**.
* **System-Viewer-Integration:** Mit dem Button `🖥️ Im System-Viewer öffnen` kann das Bild direkt in der Windows-Fotoanzeige in nativer Auflösung geöffnet werden.
* **Robuste Bildspeicherung:** Dateisperren (Windows File Locking in PIL) wurden behoben; Bilder werden speicherresistent geladen und mit eindeutigen Dateinamen am Speicherort der Druckaufträge gesichert.

### 2. 📝 Erweiterte Auftrags-Eingaben & Kundenverwaltung
* **Kunde / Kontakt:** Neues Feld zur Hinterlegung von Kunden, Auftraggebern oder Ansprechpartnern.
* **Druckparameter & Vorgaben (`specs`):** Mehrzeiliges Feld für technische Details wie Schichthöhe, Infill-Dichte, Wandstärken, Support-Einstellungen oder Filament-Typen.
* **Erweiterte Notizen:** Mehr Raum für individuelle Bemerkungen und Planungsschritte.

### 3. 🔢 Stückzahl (Quantity) & Batch-Berechnung
* **Mengenfeld (Stückzahl):** Beliebige Stückzahlen pro Druckauftrag einstellbar (Standard: 1 Stk.).
* **Automatische Skalierung:**
  * Druckzeit, Materialgewicht und Gesamtkosten werden sowohl pro Einzelstück als auch als Gesamtauftrag (`GESAMT (X Stk.)`) berechnet.
* **Multi-Deduction:** Beim Klick auf *"Als erledigt markieren & abbuchen"* wird die geplante Filamentmenge und Druckzeit automatisch mit der Stückzahl multipliziert und vom Spulenlager abgebucht.

### 4. 💰 Ist-Verkaufspreise & Gewinn-Tracking
* **Neues Feld `Ist-Verkaufspreis / Erlös`:** Ermöglicht die Erfassung des tatsächlichen Preises, zu dem ein Modell verkauft wurde.
* **Live-Gewinnberechnung:**
  * Sofortige Anzeige des echten Gewinns (`+X.XX €` in Grün bzw. Verlust in Rot) gegenüber den Selbstkosten (Material + Strom + Verschleiß + Sonstiges).
* **Ordner-KPIs im Projektverlauf:**
  * Die Ordnerübersicht fasst alle Aufträge zusammen: Gesamtaufträge (erledigt/geplant), Gesamtgewicht, Druckzeit, Gesamtkosten (EK), kalkulierter VK sowie tatsächlicher Ist-Erlös und Reingewinn.

### 5. 🔤 Ordner sortieren & verschieben im Projektverlauf
* **Alphabetische Sortierung:** Mit einem Klick Ordner aufsteigend (`🔤 A-Z`) oder absteigend (`🔤 Z-A`) sortieren.
* **Manuelle Reihenfolge:** Über `🔼` und `🔽` in der Toolbar oder im Kontextmenü lassen sich Ordner gezielt verschieben.
* **Drag & Drop:** Bestehende Druckaufträge können weiterhin per Maus zwischen Ordnern verschoben werden.

---

## 🛠️ Technische Verbesserungen & Fixes
* **Zentraler Pfad für Bilder:** `data_manager.get_images_dir()` stellt sicher, dass `job_images` immer exakt neben `print_jobs.json` verwaltet wird.
* **Windows File-Locking Fix:** Vermeidung von `WinError 32` beim Überschreiben von Vorschaubildern.
* **Unit Tests:** Testabdeckung für Mengen-Skalierung, Ist-Preise und Ordnersortierung ergänzt (alle 48 Tests erfolgreich).
