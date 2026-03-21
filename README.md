# 🧵 VibeSpool - Das smarte Filament-Management-System

Willkommen bei **VibeSpool**! Dieses Tool hilft dir dabei, den ultimativen Überblick über all deine 3D-Druck Filamente zu behalten. Egal ob im Regal, im AMS oder in der Trockenbox – mit VibeSpool weißt du immer genau, wie viel Restgewicht auf welcher Spule ist und wo sie sich gerade befindet.

![VibeSpool Screenshot](https://metalizer.de/Vibespool.jpg)

## ✨ Die Highlights (Neu in v1.6)

* **💻 Cross-Platform Sync:** VibeSpool speichert alles in universellen JSON-Dateien. Lege deinen Datenbank-Ordner einfach auf ein NAS, OneDrive oder einen USB-Stick und greife von überall darauf zu.
* **🎨 Grenzenlose Farbwahl:** Neben den Standardfarben gibt es jetzt einen manuellen Color-Picker. Klicke auf das "🎨"-Symbol, wähle deine exakte Herstellerfarbe (z.B. "Tiefsee-Blau") und VibeSpool merkt sich den Code für die grafische Ansicht.
* **📊 Smarte Excel-Filter:** Vergiss starre Buttons! Nutze dynamische Dropdown-Filter für Material, Farbe und Lagerort. Das System lernt mit: Neue Materialien werden automatisch erkannt und dem Filter hinzugefügt.
* **📦 Erweiterte, scrollbare Übersicht:** Die grafische Regal- & AMS-Ansicht skaliert jetzt intelligent mit deinen Beständen. XXL-Regale (20+ Fächer) lassen sich bequem per horizontalem Scrollbalken bedienen. Auch Kisten, Trockner oder Lager werden sauber visualisiert.
* **⚖️ Idiotensichere Gewichts-Logik:** Trage einfach das "Gewicht auf der Waage" ein und wähle den Spulentyp (Pappe, Plastik, etc.) aus. VibeSpool berechnet anhand des hinterlegten Original-Inhalts sofort dein Netto-Restgewicht.
* **🔄 In-App Updates:** Das Programm prüft ab sofort selbstständig auf GitHub, ob eine neue Version verfügbar ist, und informiert dich bequem per Pop-up.

## 🚀 Installation & Start (Für Endanwender)

Du musst nicht programmieren können, um VibeSpool zu nutzen!

1. Gehe rechts auf dieser Seite unter **[Releases](https://github.com/SirMetalizer/VibeSpool/releases)**.
2. Lade dir die neueste Version für dein Betriebssystem herunter:
    * **Windows:** Lade die `VibeSpool_Win.exe` herunter und starte sie einfach. (Keine Installation nötig!)
    * **Mac:** Lade die `VibeSpool_Mac.zip` herunter, entpacke sie und starte die App.
3. **Daten-Sicherheit:** Standardmäßig speichert die App alles lokal in deinem Benutzerverzeichnis unter `VibeSpool_Daten`. Du kannst diesen Pfad in den Einstellungen jederzeit auf dein NAS oder eine Cloud (Dropbox/OneDrive) ändern.

## 🛠️ Für Entwickler

Möchtest du am Code mitbasteln? Sehr gerne! Das Projekt ist in Python mit `Tkinter` (UI) geschrieben.

1. Klone das Repository:
    ```bash
    git clone [https://github.com/SirMetalizer/VibeSpool.git](https://github.com/SirMetalizer/VibeSpool.git)
    ```
2. Installiere die nötigen Pakete:
    ```bash
    pip install pillow qrcode
    ```
3. Starte das Programm:
    ```bash
    python filament_gui.py
    ```

## ❤️ Unterstützung & Affiliate

VibeSpool ist zu 100 % kostenlos und ein Community-Projekt. In den Einstellungen der App kannst du optional die Funktion "Entwickler mit Affiliate-Links unterstützen" aktivieren. Dies fügt bei Links zum Bambu Lab Shop automatisch einen Partner-Code an. Das kostet dich keinen Cent extra, hilft aber enorm bei der Deckung der Serverkosten und der Weiterentwicklung!

## 🐛 Bugs & Feedback

Du hast eine Idee oder einen Fehler gefunden? 
Erstelle gerne einen neuen Eintrag im Reiter **[Issues](https://github.com/SirMetalizer/VibeSpool/issues)** hier auf GitHub!
