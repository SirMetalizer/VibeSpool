# 🧵 VibeSpool - Das smarte Filament-Management-System

Willkommen bei **VibeSpool**! Dieses Tool hilft dir dabei, den ultimativen Überblick über all deine 3D-Druck Filamente zu behalten. Egal ob im Regal, im AMS oder in der Trockenbox – mit VibeSpool weißt du immer genau, wie viel Restgewicht auf welcher Spule ist und wo sie sich gerade befindet.

![VibeSpool Screenshot](https://metalizer.de/Vibespool.jpg)

## ✨ Die wichtigsten Features

* 📦 **Multi-Regal & AMS-Verwaltung:** Lege beliebig viele Regale an und bestimme selbst, wie viele Fächer sie haben. Deine Spulen werden in einer schicken grafischen Übersicht dargestellt.
* ⚖️ **Automatische Restgewicht-Berechnung:** Gib das Leergewicht der Spule und das aktuelle Bruttogewicht ein – VibeSpool berechnet auf das Gramm genau, wie viel Filament noch nutzbar ist.
* 🛒 **Integrierte Einkaufsliste & ERP-Daten:** Pflege Preise, Lieferanten und Links. Mit einem Klick landen leere Spulen auf der Einkaufsliste, die du direkt anklicken oder als CSV exportieren kannst.
* 📱 **QR-Code Generator:** Erstelle für jede Spule einen eigenen QR-Code für den schnellen Abruf und die Integration in dein lokales System.
* 🔄 **Smarte Sortierung & Updates:** "Natural Sorting" sorgt dafür, dass Fächer logisch sortiert werden (1, 2, 3... 10, 11). Mit dem integrierten Update-Checker bleibst du auf Knopfdruck immer auf dem neuesten Stand.
* 🌙 **Dark Mode & Multi-Monitor-Support:** Ergonomische Oberfläche, die deine Augen schont und sich perfekt auf verschiedenen Monitoren verhält.

## 🚀 Installation & Start (Für Endanwender)

Du musst nicht programmieren können, um VibeSpool zu nutzen!

1. Gehe rechts auf dieser Seite unter **[Releases](https://github.com/SirMetalizer/VibeSpool/releases)**.
2. Lade dir die neueste Version für dein Betriebssystem herunter:
   * **Windows:** Lade die `VibeSpool_Win.exe` herunter und starte sie einfach. (Es ist keine Installation nötig!)
   * **Mac:** Lade die `VibeSpool_Mac.zip` herunter, entpacke sie und starte die App.
3. Die App legt automatisch einen Ordner `VibeSpool_Daten` in deinem Benutzerverzeichnis an. Dort wird deine Datenbank sicher lokal auf deinem PC gespeichert.

## 🛠️ Für Entwickler

Möchtest du am Code mitbasteln? Sehr gerne! Das Projekt ist in Python mit `Tkinter` (UI) geschrieben.

1. Klone das Repository: `git clone https://github.com/SirMetalizer/VibeSpool.git`
2. Installiere die nötigen Pakete:
   ```bash
   pip install pillow qrcode
