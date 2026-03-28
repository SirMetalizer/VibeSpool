# ❓ VibeSpool - Häufig gestellte Fragen (FAQ)

Hier findest du Antworten auf die häufigsten Fragen rund um die Einrichtung und Nutzung von VibeSpool.

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