📋 Das VibeSpool Projekt-Backlog (Stand: Nach v1.4.2)
🌟 1. Das "Community-Update" (v1.5)

Excel-Filter (Dropdowns): Über der Haupttabelle kommen drei schicke Dropdown-Menüs hin (z. B. [Alle Materialien], [Alle Farben], [Alle Orte]), mit denen man die Liste mit einem Klick filtern kann wie in Excel.

Erweiterte Regal-Ansicht: In der grafischen Regal-Übersicht werden ganz unten auch alle "restlichen" Spulen (die in Kisten oder im Trockner liegen) übersichtlich in kleinen Boxen aufgelistet.

Füllmenge (Neu-Gewicht): Ein neues Eingabefeld im Tab "Basis & Lager", in das man das Neu-Gewicht der Spule (z. B. 1000g oder 250g) eintragen kann. Das ist extrem wichtig für die exakte Gramm-Preis-Berechnung später!

Dynamische Material-Liste: Wenn jemand ein neues Material (z. B. "Nylon-Carbon") per Hand in das Dropdown tippt, merkt sich das Programm das Wort dauerhaft und fügt es für die Zukunft fest in die Auswahlliste ein.

(Hinweis zum QR-Code: Den drucken wir weiterhin "statisch", damit er nicht nach jedem Druck neu ausgedruckt werden muss. Aber wir könnten eine "Live-Scan-Ansicht" bauen: Man scannt den Code am PC und es ploppt ein riesiges Fenster auf, das live das aktuelle Restgewicht und den Ort anzeigt!)

🔄 2. Workflow & Handling

Spulen-Swap (AMS <-> Regal): Ein "Tauschen"-Button. Wenn man eine Rolle aus dem Regal ins AMS legt und umgekehrt, tauschen die beiden Einträge per Klick ihre Lagerorte/Slots, ohne dass man beide einzeln umtippen muss.

🚀 3. Installation & Updates

1-Klick Auto-Updater: Wenn eine neue Version verfügbar ist, lädt VibeSpool die neue .exe im Hintergrund herunter. Ein kleines Skript beendet das Programm, tauscht die Dateien automatisch aus und startet die neue Version sofort wieder.

📷 4. Scanner & QR-Code Features

Lesbare QR-Codes: Der generierte QR-Code soll einen lesbaren Satz (z. B. ID: 1 | YUANEANG | PLA | Black/Red) fürs Handy enthalten, statt nur die nackte Zahl.

Intelligentes Quick-ID-Feld: Das Suchfeld muss umprogrammiert werden, damit es die ID automatisch aus diesen neuen, langen Sätzen herausfiltert (für Hardware-Handscanner am PC).

Webcam-Integration: Ein Button in der App, der die PC-Webcam aktiviert, um QR-Codes direkt am Bildschirm scannen zu können.

🧮 5. Tools & Rechner

Druckkosten-Rechner: Ein eingebautes Tool. Man wählt eine Rolle aus dem Bestand, tippt die Gramm-Zahl und Druckzeit aus dem Slicer ein, und das Programm berechnet die exakten Druckkosten.

Color-Picker für Filamentfarben: Echten Hex-Color-Picker einbauen, damit Nutzer exotische Farben exakt abbilden können.

📱 6. Plattformen / IoT (Zukunftsmusik)

Web-App / Mobile Nutzung: VibeSpool als lokalen "Server" (Flask) aufsetzen, damit man mit dem Smartphone-Browser im selben WLAN darauf zugreifen kann.

IoT Smart-Scale: Schnittstelle für eine WLAN-Waage mit Kamera.