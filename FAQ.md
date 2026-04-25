# ❓ VibeSpool - Häufig gestellte Fragen (FAQ)

Hier findest du Antworten auf die häufigsten Fragen rund um die Einrichtung und Nutzung von VibeSpool. 
*Tipp: VibeSpool hat auch ein eingebautes Handbuch! Klicke einfach links unten auf den **"❓ Hilfe"** Button im Programm.*

### ☁️ Wie nutze ich den Bambu Cloud Sync?
Sobald du die Cloud in den Optionen aktiviert hast, klickst du links auf **☁️ Cloud** und wählst den sicheren Browser-Login aus. VibeSpool lädt dann deine letzten erfolgreichen Drucke herunter. Klicke doppelt auf einen erledigten Druck. VibeSpool schlägt dir dank dem neuen "Smart AMS Memory" sofort die Spule vor, die **zum exakten Zeitpunkt des Drucks** im Drucker lag! Kleine Testdrucke kannst du mit "Ignorieren" bequem aus der Liste ausblenden.

### 💰 Wie berechnet VibeSpool meine Druckkosten?
VibeSpool schätzt nicht, sondern rechnet wie ein ERP-System mit harten Fakten:
1. **Material:** Das System kennt den Kaufpreis deiner Spule und das Nettogewicht.
2. **Strom:** Trage deinen kWh-Preis sowie den Stromverbrauch deines Druckers (z.B. 150 Watt) ein. 
3. **Maschinenverschleiß & Marge (Neu ab v2.0):** Trage eine Pauschale für den Druckerverschleiß pro Stunde und deine gewünschte Gewinnmarge (%) ein.
VibeSpool misst die exakte Druckzeit und addiert alle Werte zu einem finalen Verkaufspreis in Echtzeit zusammen!

### 🧮 Wie berechne ich ein Angebot für einen Kunden (ohne Spule)?
Wenn dich jemand fragt "Was würde Teil X kosten?", klicke einfach links im Menü auf das **🧮 Kalkulator** Symbol (Quick-Cost Rechner). Trage Materialpreis, Gramm und Druckzeit ein – VibeSpool spuckt dir in einer Sekunde den perfekten Verkaufspreis inklusive deiner Marge aus.

### ⚖️ Ich habe eine exotische Spule, für die sich keine Vorlage lohnt. Was tun?
Dafür gibt es das **individuelle Leergewicht** (Einweg-Spule):
Trage das Netto-Gewicht (z.B. 1000g) und das Brutto-Gewicht von deiner Waage (z.B. 1202g) in die Felder ein. Klicke dann auf den kleinen **🧮 Button** direkt neben der Dropdown-Liste für Leerspulen. VibeSpool berechnet die 202g Differenz und speichert sie unsichtbar *nur* für dieses eine Filament ab!

### ⏳ Kann ich die Kosten für sehr alte Drucke nachträglich berechnen?
Ja! Das ist die "Retro-Fit" Funktion. 
Gehe links auf **📊 Finanzen**. Unten in der globalen Historie machst du einen **Doppelklick** auf einen alten Druck. Es öffnet sich ein Bearbeitungs-Fenster. Klicke dort einfach auf **"🧮 Mat."** und danach auf **"🧮 Marge"**. VibeSpool zieht sich die Daten aus der Vergangenheit und rechnet das Angebot auf den Cent genau nach!

### 🛠️ Ich habe mich beim Verbrauch vertippt. Wie korrigiere ich das?
Ebenfalls über das Finanz-Dashboard (**📊 Finanzen**). Doppelklicke den falschen Eintrag in der Historie unten und ändere die Grammzahl. VibeSpool besitzt ein **"Auto-Heal"** Feature: Es korrigiert magisch das Gewicht deiner Spule im Regal und repariert automatisch den falschen Tag in deinem 7-Tage-Balkendiagramm!

### 📖 Wo sehe ich den Lebenslauf einer Spule?
Mache einen **Rechtsklick** auf eine beliebige Spule in deiner Tabelle und wähle **📜 Spulen-Logbuch öffnen**. Dort siehst du einen detaillierten Kontoauszug.

### 📥 Wie importiere ich meine alte Excel-Liste?
Du musst nicht alles neu abtippen! Nutze einfach unsere fertige CSV-Vorlage:
1. Lade dir die `VibeSpool_Import_Vorlage.csv` aus den Dateien herunter oder nutze die [Google Sheets Vorlage](https://docs.google.com/spreadsheets/d/1ko-vQtDF6rNkR7Vq5q1HUZ2xhHl_6P_uVhrKrvehpLU/edit?gid=1380756208#gid=1380756208).
2. Fülle die Tabelle in Excel/Calc aus.
3. Speichere die Datei als `.csv` ab.
4. Klicke in VibeSpool oben rechts auf **"📥 CSV Import"** und wähle die Datei aus!

### 🎨 Wie kann ich eigene Materialien (z.B. PAHT-CF) oder Farben hinzufügen?
Du kannst die Dropdown-Listen in VibeSpool jederzeit um deine eigenen Spezial-Sorten erweitern:
* Gehe oben rechts auf **⚙ Optionen** -> **📋 Listen**.
* Dort kannst du flexibel neue Materialien, Farben oder Hersteller hinzufügen. **Tipp:** VibeSpool sortiert diese Listen im Hauptfenster ab sofort automatisch von A bis Z!

### 🏷️ Wie kann ich meine Regalfächer (z.B. "Fach 1") umbenennen?
Wenn du deinen Fächern eigene Namen wie "Bambu PLA" geben möchtest:
* Gehe in die **⚙ Optionen**.
* Wähle den Reiter **📦 Lager** und klicke unten auf **"🏷️ Fächer benennen"**.
* Trage deine Wunschnamen ein und speichere. VibeSpool passt alle bereits im Regal liegenden Spulen automatisch an!

### 📁 Wo wird meine Datenbank gespeichert?
VibeSpool speichert alle Daten standardmäßig lokal in dem Ordner, in dem sich auch das Programm befindet. Du kannst den Speicherort jedoch jederzeit ändern (z.B. auf ein NAS oder in deine Dropbox):
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
* Wähle den Reiter **🤖 Drucker**.
* Trage bei "Anzahl AMS Einheiten" die entsprechende Zahl ein und speichere. Die neuen Slots tauchen danach sofort im Programm auf.

### 🔍 Wofür ist das Feld "Quick-ID" oben in der Leiste?
Das Feld ist dein universeller Omni-Scanner! Für alle Maker gedacht, die RFID-Tags oder QR-Codes nutzen:
* Scanne VibeSpool-IDs, RFID-Chips oder sogar **originale 1D-Hersteller-Barcodes** (auf der Filament-Box). 
* Wenn du einen neuen Hersteller-Strichcode einscannst, speichert VibeSpool ihn. Beim nächsten Scan wird die Marke sofort erkannt ("Smart Learning")!

### 🛡️ Windows Defender schlägt Alarm und blockiert den Download. Ist VibeSpool ein Virus?
**Nein, VibeSpool ist zu 100 % sicher und quelloffen.** Da VibeSpool in Python programmiert ist und für Windows in eine kompakte `.exe`-Datei verpackt wird (mit *PyInstaller*), entpackt sich das Programm beim Start kurzzeitig im Hintergrund. Windows Defender und andere KI-basierte Scanner stufen dieses Verhalten oft fälschlicherweise als verdächtig ein (ein sogenannter *False Positive*). Du kannst in den Windows Defender Details auf "Trotzdem ausführen" klicken. Der gesamte Quellcode ist auf GitHub öffentlich einsehbar – es gibt keine versteckten Funktionen!

### 🖨️ Wie drucke ich Etiketten für meine Spulen?
VibeSpool hat einen integrierten "Label Creator" mit PDF-Export!
* Klicke im Menü auf der linken Seite auf das **🏷️ Label** Icon.
* Wähle die gewünschte Spule aus der Liste aus. Das Programm generiert sofort ein fertiges Etikett mit QR-Code (VibeSpool ID), Material, Farbe und Drucktemperaturen.
* **Tipp:** Du kannst entweder ein einzelnes Label als PNG speichern oder über **"📑 ALLE als PDF exportieren"** blitzschnell fertige DIN A4 Bögen oder Formate für Rollen-Etikettendrucker generieren!

### 📦 Mein Regal ist sehr tief (2 Spulen stehen hintereinander). Geht das?
Ja, VibeSpool unterstützt sogenannte "Doppeltiefe Regale"!
* Gehe in die **⚙ Optionen**.
* Setze im Reiter **📦 Lager** den Haken bei "Doppeltiefe Regale (2 Rollen pro Slot)" und speichere.
* VibeSpool teilt ab sofort jeden Slot in "Vorne (V)" und "Hinten (H)" auf. In der grafischen Regalansicht werden diese übersichtlich übereinander gestapelt dargestellt. Deine bereits vorhandenen Spulen werden dabei automatisch sicher nach vorne geschoben.

### 🖱️ Wie kann ich das Layout der Haupttabelle anpassen?
Wenn dein Monitor klein ist, kannst du unnötige Spalten einfach ausblenden:
* Mache einen **Rechtsklick** oben auf die Tabellen-Kopfzeile.
* Im aufpoppenden Menü kannst du Haken setzen oder entfernen. VibeSpool merkt sich diese Einstellung beim nächsten Start.

### ⚡ Gibt es eine schnellere Methode, Spulen zu verwalten?
Ja! Das **Quick-Action Menü**:
* Mache einen **Rechtsklick** direkt auf eine Spule in der Liste.
* Du kannst die Spule sofort ins AMS schieben, klonen, das Logbuch öffnen oder als "Leer" markieren, ohne die Felder links zu benutzen.

### 📉 Ich habe beim Slicer-Verbrauch zu viel abgezogen. Was nun?
Neben dem "➖ Abziehen" Button findest du den **"➕ Korrektur"** Button.
* Tippe den Differenzbetrag in das Feld und klicke auf "➕ Korrektur".
* Das Gewicht wird zurückgebucht und die Statistik (sowie das Spulen-Logbuch) wird im Hintergrund sauber korrigiert!

### 📊 Wo sehe ich, wie viel Filament ich verdruckt habe?
* Klicke links im Hauptmenü auf **"📊 Finanzen"**.
* Es öffnet sich das große **Unified Analytics Dashboard**. 
* Hier siehst du ein interaktives 7-Tage-Balkendiagramm, deinen Gesamtwert im Lager und den genauen Durchschnittspreis pro Kilogramm für jedes deiner Materialien.

### 📡 Was passiert mit meinen MQTT Daten bei WLAN-Ausfall?
Nichts geht verloren! VibeSpool hat einen **Offline-Buffer**. Das Programm speichert die Daten lokal auf der Festplatte und sendet sie im Hintergrund automatisch an deinen Home Assistant nach, sobald die Verbindung wieder steht.