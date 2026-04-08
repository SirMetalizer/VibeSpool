# ❓ VibeSpool - Häufig gestellte Fragen (FAQ)

Hier findest du Antworten auf die häufigsten Fragen rund um die Einrichtung und Nutzung von VibeSpool.

### 📥 Wie importiere ich meine alte Excel-Liste?
Du musst nicht alles neu abtippen! Nutze einfach unsere fertige CSV-Vorlage:
1. Lade dir die `VibeSpool_Import_Vorlage.csv` aus den Dateien herunter oder nutze die [Google Sheets Vorlage](https://docs.google.com/spreadsheets/d/1ko-vQtDF6rNkR7Vq5q1HUZ2xhHl_6P_uVhrKrvehpLU/edit?gid=1380756208#gid=1380756208) (Dort auf "Datei" -> "Herunterladen" -> "CSV" klicken).
2. Fülle die Tabelle in Excel/Calc mit deinen Filamenten aus (bitte die Spaltennamen in der ersten Zeile nicht verändern).
3. Speichere die Datei als `.csv` ab.
4. Klicke in VibeSpool oben rechts auf **"📥 CSV Import"** und wähle die Datei aus!

### 🎨 Wie kann ich eigene Materialien (z.B. PAHT-CF) oder Farben hinzufügen?
Du kannst die Dropdown-Listen in VibeSpool jederzeit um deine eigenen Spezial-Sorten erweitern:
* Gehe oben rechts auf **⚙ Optionen**.
* Wähle den neuen Reiter **📋 Listen**.
* Dort kannst du ganz flexibel neue Materialien, Farben oder Effekte hinzufügen und alte löschen.

### 🏷️ Wie kann ich meine Regalfächer (z.B. "Fach 1") umbenennen?
Wenn du deinen Fächern eigene Namen wie "Bambu PLA" geben möchtest:
* Gehe in die **⚙ Optionen**.
* Wähle den Reiter **📦 Lager** und klicke unten auf **"🏷️ Fächer benennen"**.
* Trage deine Wunschnamen ein und speichere. VibeSpool passt alle bereits im Regal liegenden Spulen automatisch an!

### 📁 Wo wird meine Datenbank gespeichert?
VibeSpool speichert alle Daten standardmäßig lokal in dem Ordner, in dem sich auch das Programm befindet. 
Du kannst den Speicherort jedoch jederzeit ändern (z.B. auf ein NAS oder in deine Dropbox):
* Gehe oben rechts auf **⚙ Optionen**.
* Wähle den Reiter **⚙ System**.
* Unter "Daten-Pfad" kannst du einen eigenen Ordner festlegen.

### ⚖️ Warum kann ich kein Leergewicht / keine Spule auswählen?
Das Dropdown-Menü für das Spulen-Leergewicht ist anfangs leer, da es unzählige verschiedene Spulentypen gibt.
* Klicke im linken Menü auf das Spulen-Icon (**🧵 Leerspulen verwalten**).
* Klicke auf **📋 Vorlagen**.
* Wähle die Marken aus, die du besitzt, und importiere sie. Ab sofort stehen sie dir im Hauptfenster zur Verfügung!

### 🤔 Warum ist mein Netto-Gewicht exakt gleich dem Brutto-Gewicht?
Das passiert, wenn du VibeSpool nicht gesagt hast, welche Leerspule du verwendest. Das Programm zieht in diesem Fall `0g` für die Spule ab. Sobald du im Feld "Spule / Leergewicht" eine Vorlage auswählst (z.B. Bambu Lab mit 250g), wird das Netto-Gewicht sofort korrekt berechnet.

### 📦 Ich habe mehr als ein AMS, wie trage ich das ein?
Standardmäßig geht VibeSpool von einem AMS aus. Wenn du 2, 3 oder 4 Stück hast (oder einen AMS Lite):
* Gehe in die **⚙ Optionen**.
* Wähle den Reiter **🔌 Hardware**.
* Trage bei "Anzahl AMS Einheiten" die entsprechende Zahl ein und speichere. Die neuen Slots tauchen danach sofort im Programm auf.

### 🔍 Wofür ist das Feld "Quick-ID" oben in der Leiste?
Das Feld ist für alle Maker gedacht, die RFID-Tags oder QR-Codes auf ihre Spulen/Boxen kleben. 
Du kannst den Code einfach mit einem Barcode-Scanner (oder der Webcam über den Kamera-Button) einscannen, und VibeSpool markiert sofort die richtige Spule in deiner Liste. Man muss sich die IDs also nicht merken!

### 🛡️ Windows Defender schlägt Alarm und blockiert den Download. Ist VibeSpool ein Virus?
**Nein, VibeSpool ist zu 100 % sicher und quelloffen.** Da VibeSpool in Python programmiert ist und für Windows in eine kompakte `.exe`-Datei verpackt wird (mit *PyInstaller*), entpackt sich das Programm beim Start kurzzeitig im Hintergrund. Windows Defender und andere KI-basierte Scanner stufen dieses Verhalten oft fälschlicherweise als verdächtig ein (ein sogenannter *False Positive*). 
Du kannst in den Windows Defender Details auf "Trotzdem ausführen" klicken. Der gesamte Quellcode ist hier auf GitHub öffentlich einsehbar – es gibt keine versteckten Funktionen!

### 🖨️ Wie drucke ich Etiketten für meine Spulen?
VibeSpool hat einen integrierten "Label Creator"!
* Klicke im Menü auf der linken Seite auf das **🏷️ Label** Icon.
* Wähle die gewünschte Spule aus der Liste aus.
* Das Programm generiert sofort ein fertiges Etikett mit QR-Code (VibeSpool ID), Material, Farbe und Drucktemperaturen.
* Klicke auf "Als PNG speichern". Du kannst dieses Bild dann mit jedem Standard-Drucker oder Etikettendrucker (z.B. Brother, Dymo) ausdrucken und auf deine Spule kleben!

### 📦 Mein Regal ist sehr tief (2 Spulen stehen hintereinander). Geht das?
Ja, VibeSpool unterstützt sogenannte "Doppeltiefe Regale"!
* Gehe in die **⚙ Optionen**.
* Setze im Reiter **📦 Lager** ganz unten den Haken bei "Doppeltiefe Regale (2 Rollen pro Slot)" und speichere.
* VibeSpool teilt ab sofort jeden Slot in "Vorne (V)" und "Hinten (H)" auf. In der grafischen Regalansicht werden diese übersichtlich übereinander gestapelt dargestellt. Deine bereits vorhandenen Spulen werden dabei automatisch sicher nach vorne geschoben.

### 🖱️ Wie kann ich das Layout der Haupttabelle anpassen?
Wenn dein Monitor klein ist, kannst du Spalten ausblenden:
* Mache einfach einen **Rechtsklick** oben auf die Tabellen-Kopfzeile.
* Im aufpoppenden Menü kannst du Haken setzen oder entfernen.

### ⚡ Gibt es eine schnellere Methode, Spulen zu verwalten?
Ja! Das **Quick-Action Menü**:
* Mache einen **Rechtsklick** direkt auf eine Spule in der Liste.
* Du kannst die Spule sofort ins AMS schieben, klonen oder als "Leer" markieren.

### 📉 Ich habe beim Slicer-Verbrauch zu viel abgezogen. Was nun?
Neben dem "➖ Abziehen" Button findest du jetzt den **"➕ Korrektur"** Button.
* Tippe den Differenzbetrag in das Feld und klicke auf "➕ Korrektur".
* Das Gewicht wird zurückgebucht und die Statistik wird im Hintergrund sauber korrigiert!

### 📊 Wo sehe ich, wie viel Filament ich verdruckt habe?
* Klicke links im Hauptmenü auf **"📊 Finanzen"**.
* Klicke unten auf den blauen Button **"📈 Verbrauchs-Verlauf (7 Tage)"**. 
* Hier siehst du ein Balkendiagramm deines Materialverbrauchs der letzten Woche.

### 📡 Was passiert mit meinen MQTT Daten bei WLAN-Ausfall?
Nichts geht verloren! VibeSpool hat einen **Offline-Buffer**. Das Programm speichert die Daten lokal und sendet sie automatisch nach, sobald die Verbindung wieder steht.