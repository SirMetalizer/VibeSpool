📋 Das VibeSpool Projekt-Backlog (Stand nach v1.4)

🔄 1. Workflow & Handling (Als Nächstes?)
Spulen-Swap (AMS <-> Regal): Ein "Tauschen"-Button. Wenn man eine Rolle aus dem Regal ins AMS legt und umgekehrt, tauschen die beiden Einträge per Klick ihre Lagerorte/Slots, ohne dass man beide einzeln umtippen muss.

📷 2. Scanner & QR-Code Features
Lesbare QR-Codes: Der generierte QR-Code soll einen lesbaren Satz (z. B. ID: 1 | YUANEANG | PLA | Black/Red) fürs Handy enthalten, statt nur die nackte Zahl.

Intelligentes Quick-ID-Feld: Das Suchfeld muss umprogrammiert werden, damit es die ID automatisch aus diesen neuen, langen Sätzen herausfiltert (für Hardware-Handscanner am PC).

Webcam-Integration: Ein Button in der App, der die PC-Webcam aktiviert, um QR-Codes direkt am Bildschirm scannen zu können (ohne extra Hardware-Scanner).

🧮 3. Tools & Rechner
Druckkosten-Rechner: Ein eingebautes Tool. Man wählt eine Rolle aus dem Bestand, tippt die Gramm-Zahl und Druckzeit aus dem Slicer ein, und das Programm berechnet die exakten Druckkosten (inklusive Strompreis-Kalkulation).

📱 4. Plattformen / IoT (Zukunftsmusik)
Web-App / Mobile Nutzung: VibeSpool als lokalen "Server" (Flask) aufsetzen, damit man mit dem Smartphone-Browser darauf zugreifen kann.

IoT Smart-Scale: Schnittstelle für eine WLAN-Waage mit Kamera (ESP32 + HX711). Rolle draufstellen -> automatisch scannen -> VibeSpool aktualisiert das Gewicht.
