### 📋 Das VibeSpool Projekt-Backlog (Roadmap für kommende Versionen)

#### 🌟 1. Das "Community-Update" (Feedback von Patrick)

* **Excel-Filter (Dropdowns):** Über der Haupttabelle kommen drei schicke Dropdown-Menüs hin (z. B. `[Alle Materialien]`, `[Alle Farben]`, `[Alle Orte]`), mit denen man die Liste mit einem Klick filtern kann wie in Excel.
* **Erweiterte Regal-Ansicht:** In der grafischen Regal-Übersicht werden ganz unten auch alle "restlichen" Spulen (die in Kisten oder im Trockner liegen) übersichtlich in kleinen Boxen aufgelistet.
* **Füllmenge (Neu-Gewicht):** Ein neues Eingabefeld im Tab "Basis & Lager", in das man das Neu-Gewicht der gekauften Spule (z. B. 1000g oder 250g) eintragen kann.
* **Dynamische Material-Liste:** Wenn jemand ein neues Material (z. B. "Nylon-Carbon") per Hand in das Dropdown tippt, merkt sich das Programm das Wort dauerhaft und fügt es für die Zukunft fest in die Auswahlliste ein.

#### 🔄 2. Workflow & Handling

* **Spulen-Swap (AMS <-> Regal):** Ein "Tauschen"-Button. Wenn man eine Rolle aus dem Regal ins AMS legt und umgekehrt, tauschen die beiden Einträge per Klick ihre Lagerorte/Slots, ohne dass man beide einzeln manuell umtippen muss.

#### 🚀 3. Installation & Updates

* **1-Klick Auto-Updater:** Wenn eine neue Version verfügbar ist, lädt VibeSpool die neue `.exe` im Hintergrund herunter. Ein kleines, unsichtbares Skript beendet das Programm, tauscht die Dateien automatisch aus und startet die neue Version sofort wieder – echtes One-Click-Update!

#### 📷 4. Scanner & QR-Code Features

* **Lesbare QR-Codes:** Der generierte QR-Code soll einen lesbaren Satz (z. B. `ID: 1 | YUANEANG | PLA | Black/Red`) fürs Handy enthalten, statt nur die nackte Zahl.
* **Intelligentes Quick-ID-Feld:** Das Suchfeld oben wird so umprogrammiert, dass es die reine ID automatisch aus diesen neuen, langen Sätzen herausfiltert (perfekt für Hardware-Handscanner am PC).
* **Webcam-Integration:** Ein Button in der App, der die PC-Webcam aktiviert, um QR-Codes direkt am Bildschirm scannen zu können, ohne dass man einen extra Handscanner kaufen muss.

#### 🧮 5. Tools & Rechner

* **Druckkosten-Rechner:** Ein eingebautes Tool. Man wählt eine Rolle aus dem Bestand, tippt die Gramm-Zahl und Druckzeit aus dem Slicer ein, und das Programm berechnet anhand des Rollenpreises und der Stromkosten die exakten Druckkosten.
* **Color-Picker für Filamentfarben:** Einen echten Hex-Color-Picker einbauen, damit Nutzer extrem spezifische Farben (wie "Fern Green" oder Pastell-Töne) 1:1 abbilden können.

#### 📱 6. Plattformen / IoT (Zukunftsmusik)

* **Web-App / Mobile Nutzung:** VibeSpool als lokalen "Server" (Flask) aufsetzen, damit man mit dem Smartphone-Browser im eigenen WLAN darauf zugreifen kann.
* **IoT Smart-Scale:** Schnittstelle für eine WLAN-Waage (ESP32). Rolle draufstellen -> wird automatisch erkannt und das Gewicht in VibeSpool aktualisiert.