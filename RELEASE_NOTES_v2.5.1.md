# 🚀 Release: VibeSpool v2.5.1 – Filamenttrockner & Multi-Drucker Cloud Smart-Match Update

Mit **v2.5.1** wird das Abbuchen von Materialverbräuchen über die Bambu Cloud für **Zweitdrucker** und **Filamenttrockner (Externe Spulen)** deutlich komfortabler und vollautomatisch. Außerdem enthält dieses Update Verbesserungen am Projektplaner sowie einen wichtigen Fix für den Auto-Updater.

---

## ✨ Die Highlights in Version 2.5.1

### 1. 🔥 Intelligente Filamenttrockner- & Zweitdrucker-Erkennung (Bambu Cloud Smart-Match)
* **Kein falsches Mapping auf Rolle 1-1 (`AMS 1 Slot 1`) mehr:** Wenn auf einem Zweitdrucker ohne AMS (z. B. direkt aus dem `Filamenttrockner`) einfarbig gedruckt wird, meldet Bambu Studio / die Cloud im Projekt-Mapping oft `ams: 0` oder `254`. VibeSpool erkennt nun automatisch, dass dieser Drucker kein AMS nutzt, und schlägt direkt die im **Filamenttrockner** (bzw. dem zugewiesenen externen Lagerort) liegende Spule vor.
* **Automatische Zweitdrucker-Erkennung:** Selbst wenn nur beim 1. Drucker (mit `AMS 1`) die Seriennummer eingetragen ist, erkennt VibeSpool anhand der abweichenden Cloud-`deviceId`, dass der Druckauftrag vom Zweitdrucker stammt, und wählt automatisch die Spule aus dem `Filamenttrockner`.

### 2. 🖨️ Neue Schnellauswahl „Drucker / Material-Quelle“ mit Auto-Memory
* **Direktwahl im Smart-Match:** Oben im Smart-Match-Seitenpanel gibt es jetzt das Dropdown **„🖨️ Drucker / Material-Quelle“** (sowie eine neue Spalte **„Drucker / Quelle“** in der Cloud-Historie).
* **Einmal wählen – dauerhaft merken (`cloud_device_map`):** Wählst du bei einem Cloud-Druck einmal deinen Zweitdrucker oder `📍 Direkt aus: Filamenttrockner` aus, merkt sich VibeSpool die Cloud-Geräte-ID (`deviceId`) dauerhaft für alle zukünftigen Drucke dieses Druckers!
* **Lagerort-Anzeige & Priorisierung im Dropdown:** Hinter jeder Spule im Smart-Match-Dropdown steht jetzt ihr aktueller Lagerort (z. B. `[Filamenttrockner]`, `[AMS 1-1]`), und bei externen Drucken werden Spulen aus dem Trockner ganz oben gelistet.

### 3. 🕰️ Zeitmaschine & Quick-Swap für den Filamenttrockner
* **Quick-Swap für Zusatz-Orte:** Wenn du per Quick-Swap eine neue Spule in den `Filamenttrockner` legst, wird die bisherige Spule aus dem Trockner automatisch zurück auf den frei gewordenen Regalplatz getauscht (analog zum AMS).
* **Zeitmaschine (`ams_snapshots.json`):** Protokolliert jetzt auch Spulenwechsel im `Filamenttrockner`, sodass auch ältere Cloud-Drucke noch wissen, welche Spule zum Druckzeitpunkt im Trockner lag.

### 4. 📂 Projektplaner & Auto-Updater Fixes
* **Übersichtlicher Projektplaner:** Beim Öffnen des Projektverlaufs werden standardmäßig nur die **Oberordner** angezeigt, während Unterordner und unzugeordnete Aufträge eingeklappt starten.
* **Auto-Updater Fix:** Bereinigt die temporären PyInstaller-Umgebungsvariablen (`_MEIPASS2`, `_MEIPASS`) vor dem Start der aktualisierten EXE und behebt damit den Fehler `Security validation failure: unexpected name of application's home directory`.

