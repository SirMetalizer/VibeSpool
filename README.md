# 🧵 VibeSpool - Das smarte Filament-Management-System

![Version](https://img.shields.io/badge/version-2.0.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Die smarte Schaltzentrale für dein 3D-Druck Filament-Lager.** VibeSpool ist ein lokales Desktop-Tool (Python/Tkinter), das dir die volle visuelle, mobile und kaufmännische Kontrolle über deine Spulen gibt.

<img width="1924" height="1044" alt="VibeSpool Main Dashboard" src="https://github.com/user-attachments/assets/7234891c-0458-478b-8c5a-7d9e6cd184cb" />

---

## 🆕 Was ist neu in Version 2.0.1? ("The Pop-up Killer & Print Queue Update")
Dieses Update bringt massive Verbesserungen für den Workflow und die Verwaltung eures Filament-Lagers. Wir haben das Feedback ernst genommen und nervige Pop-up-Fenster in Rente geschickt!

### ✨ Die Highlights:

* **📝 NEU: Auftrags-Planer (Print Queue & MES):**
  VibeSpool wird zur Schaltzentrale deiner Druck-Aufträge! Mit dem neuen Planungs-Tool kannst du anstehende Drucke verwalten. Weise Kunden oder Projekt-Titel zu, speichere direkte Links zu den 3D-Modellen und hinterlege genaue Notizen (z.B. "Marble für Body, Grün für Schrift").  
  **Das Highlight:** Du kannst die exakten Spulen aus deinem Inventar (inkl. Multi-Color ID 1 + ID 2) direkt dem Auftrag zuweisen!

  <img width="1068" height="747" alt="image" src="https://github.com/user-attachments/assets/720140a3-a733-4e17-bfdd-0f3322211ff3" />

* **Slide-In Panels statt Pop-up Chaos:** 
  Egal ob Kostenschnellrechner, Regal-Konfigurator oder Bambu-Cloud-Sync: Alle Werkzeuge öffnen sich jetzt elegant als verschiebbares Panel an der rechten Bildschirmseite! Ihr könnt die Fenster beliebig breit ziehen und habt eure Haupttabelle (oder die Lager-Vorschau) links weiterhin voll im Blick.

  <img width="1263" height="893" alt="image" src="https://github.com/user-attachments/assets/dcf05c97-76ce-4c55-8f93-b606b6a28175" />

* **Grid-Naming V2 (Die absolute Lager-Kontrolle):** 
  Ihr wolltet es, ihr bekommt es! Ab sofort könnt ihr im Regal-Planer nicht mehr nur die Reihen (Fächer) umbenennen, sondern auch jede einzelne Spalte (Slot). Wenn Slot 3 ab sofort "PLA-Spalte" heißen soll – bitteschön!

* **Magische Spulen-Umbuchung:**
  Das Beste am neuen Naming-System: Ändert ihr den Namen eines Fachs oder Slots, sucht VibeSpool im Hintergrund automatisch alle Spulen, die dort liegen, und bucht sie live auf den neuen Namen um. Kein manuelles Anpassen mehr nötig!

* **Live-Updates (Keine Neustarts mehr):**
  Wenn ihr in den Einstellungen Dinge wie Doppeltiefe, Fach-Namen oder Regal-Größen ändert, müsst ihr die App danach nicht mehr neu starten. Die Haupt-Tabelle, alle Dropdown-Menüs und der Lager-Visualisierer updaten sich im selben Moment, in dem ihr auf Speichern klickt.

* **Smarterer Bambu Cloud Sync:**
  Der AMS-Sync versteht jetzt eure neuen Custom-Namen und die Doppeltiefen-Einstellung, wenn er euch Zielorte für neue Spulen vorschlägt.

---

## 🆕 Was ist neu in Version 2.0.0? ("The Enterprise & Cost Center Update")
VibeSpool macht den Sprung zum professionellen ERP-System für Gewerbetreibende und Power-User!
* **Auto-Heal & Retro-Fit:** Historien-Einträge können jetzt nachträglich bearbeitet werden. VibeSpool korrigiert das Diagramm und das Spulengewicht vollautomatisch. Alte Drucke können mit den neuen "Retro-Fit" Buttons sekundenschnell nachträglich kalkuliert werden.
* **Individuelles Leergewicht:** Für exotische Spulen kann jetzt on-the-fly ein einmaliges Leergewicht berechnet und an die Spule gebunden werden.
* **Quick-Cost Rechner:** Ein Standalone-Kalkulator, um schnell Preise für Kunden zu berechnen, ohne das Lager anzufassen.


Übersicht Finanzen:

<img width="1096" height="888" alt="image" src="https://github.com/user-attachments/assets/d6087302-53c5-4680-8416-14f69bf809c8" />

Druckhistorie aus der Bambu Cloud:

<img width="853" height="641" alt="image" src="https://github.com/user-attachments/assets/882971f5-ac53-4c55-bd49-cd73ced4ca34" />

Kostenrechner:

<img width="964" height="697" alt="image" src="https://github.com/user-attachments/assets/d56dcd36-11d0-47f3-b1d6-358f7c92ffe7" />


## ✨ Features

### ☁️ Bambu Cloud API & Smart-Match
Verbinde VibeSpool mit der Bambu Cloud. Das System lädt deine fertigen Druckaufträge herunter, erkennt automatisch, welche Spulen im AMS verwendet wurden (**Smart-Match**) und teilt den Verbrauch bei Multi-Color-Drucken grammgenau auf.

<img width="1014" height="805" alt="image" src="https://github.com/user-attachments/assets/aa1822b7-382e-4503-b4f0-0906a73616a3" />

### 📝 NEU: Auftrags-Planer (Print Queue & MES):
VibeSpool wird zur Schaltzentrale deiner Druck-Aufträge! Mit dem neuen Planungs-Tool kannst du anstehende Drucke verwalten. Weise Kunden oder Projekt-Titel zu, speichere direkte Links zu den 3D-Modellen und hinterlege genaue Notizen (z.B. "Marble für Body, Grün für Schrift").

**Das Highlight:** Du kannst die exakten Spulen aus deinem Inventar (inkl. Multi-Color ID 1 + ID 2) direkt dem Auftrag zuweisen!

<img width="1068" height="747" alt="image" src="https://github.com/user-attachments/assets/720140a3-a733-4e17-bfdd-0f3322211ff3" />

### 💰 Das Cost Center (Gewerbe-Kalkulation)
VibeSpool berechnet nicht nur Material- und Stromkosten, sondern berücksichtigt auch Maschinenverschleiß (pro Druckstunde) und schlägt automatisch deine Gewinnmarge (%) auf. Alle Drucke über alle Spulen hinweg laufen im globalen Kassenbuch zusammen. Ein Standalone Quick-Cost Rechner hilft dir bei schnellen Kundenangeboten.

### 💰 Druckkosten-Rechner & Logbuch
VibeSpool kombiniert den Kaufpreis deiner Spulen mit deinem lokalen Strompreis und der Laufzeit des Drucks. Bei jedem Cloud-Sync siehst du auf den Cent genau, was dein Druck gekostet hat. Alles wird im **Spulen-Logbuch** dauerhaft als "Kontoauszug" gespeichert.

### 📊 Unified Analytics & Auto-Heal Historie
Ein interaktives Dashboard zeigt dir den genauen Bestandswert, den Ø-Preis/kg und einen 7-Tage-Verbrauchsverlauf. Fehler beim Eintragen gemacht? Die Historie lässt sich nachträglich bearbeiten – VibeSpool repariert das Spulengewicht und das Chart automatisch (**Auto-Heal**).

### 📥 System-Tray & Hintergrund-Monitor
Schließe das Fenster und VibeSpool läuft lautlos im Windows-Tray (neben der Uhr) weiter. Es lauscht im Hintergrund auf deinen Drucker und meldet sich über smarte **Toast-Benachrichtigungen**.

### 📱 Mobile Companion & Handyscanner
VibeSpool wird kabellos! Scanne einfach den QR-Code am Monitor und dein Handy wird zum **kabellosen Handyscanner**.
* **Keine App-Installation:** Läuft direkt im Browser über deinen lokalen Webserver.
* **Hersteller-Barcodes:** Scanne Strichcodes von Originalverpackungen – VibeSpool lernt die Marken automatisch!

### ⚖️ Die Schlaue Waage
Nie wieder Leergewichte raten. Trage das Brutto-Gewicht ein, das deine Küchenwaage anzeigt. VibeSpool erkennt Hersteller und Material, zieht das korrekte Leerspulen-Gewicht ab und bucht das Netto-Gewicht ein.

### 📦 Lagerverwaltung & Doppeltiefe Regale
Bilde dein echtes Regal virtuell nach (z.B. 4 Reihen, 8 Spalten). VibeSpool unterstützt sogar **doppeltiefe Regale** (2 Spulen hintereinander) und bietet eine **Quick-Swap** Funktion, um Spulen blitzschnell ins AMS zu tauschen.

### 🏷️ Etiketten-Druck & Label Creator
Generiere automatisch fertige Etiketten mit QR-Codes, Drucktemperaturen und Farben. Exportiere sie als PNG oder direkt als **PDF-Bögen** für DIN A4 oder Rollen-Etikettendrucker.

### 🤖 Bambu AMS Live-Sync via MQTT
Gleiche dein Lager live im lokalen Netzwerk mit deinem Bambu Lab AMS ab. VibeSpool liest aus, welche Farbe und welches Material aktuell in welchem Slot steckt.

### 📋 Listen-Verwaltung & CSV-Import
Füge eigene Materialien (z.B. PAHT-CF), Farben oder Effekte flexibel hinzu. Importiere deine alten Excel-Tabellen bequem über die integrierte CSV-Schnittstelle.


## 🚀 Installation & Start

### Für Nutzer (Windows & Mac)
1. Lade dir die neuste Version unter [Releases](https://github.com/SirMetalizer/VibeSpool/releases/latest) herunter.
2. Starte die **`VibeSpool_Win.exe`** (oder `.app` auf dem Mac) – keine Installation von Python nötig!

### Für Entwickler
Stelle sicher, dass **Python 3.10+** installiert ist.

1. **Repository klonen:**

  ```bash
git clone [https://github.com/SirMetalizer/VibeSpool.git](https://github.com/SirMetalizer/VibeSpool.git)
cd VibeSpool
   ```

Abhängigkeiten installieren:

   ```bash
pip install Pillow pyzbar opencv-python qrcode paho-mqtt pystray requests
   ```
Starten:

   ```bash
python filament_gui.py
   ```

## 🆕 Was ist neu in Version 1.10.0? ("The Smart Pro Update")
Bambu Cloud & Smart-Match: Abzüge aus der Cloud werden jetzt vollautomatisch den richtigen AMS-Slots zugewiesen.

* **Finanz-Dashboard**: Reale Berechnung von Strom- und Materialkosten pro Druck. Neues Unified-Dashboard mit Preis/kg Auswertung.

* **Spulen-Logbuch**: Detaillierte Historie für jede einzelne Spule (Wann, wie viel, wie teuer).

* **In-App Handbuch**: Ein integriertes Mini-Wiki erklärt alle Features direkt im Programm.

* **System-Tray**: Die App kann nun minimiert im Hintergrund weiterlaufen.

## 🤝 Support & Spenden
VibeSpool ist ein Open-Source Hobbyprojekt. Wenn dir das Tool hilft, freue ich mich riesig über einen virtuellen Kaffee!

**Entwickelt von SirMetalizer | Mit speziellem Dank an Lena (Lead Inspiration & UX Design) & Kathi💡**
