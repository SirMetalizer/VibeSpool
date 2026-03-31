# 🍏 VibeSpool auf macOS – Installations-Guide

Da es für macOS aktuell (noch) keine fertige "Doppelklick-App" gibt, wird VibeSpool auf dem Mac direkt aus dem sogenannten Quellcode gestartet. Das klingt nach Matrix-Hacking, ist aber in 5 Minuten erledigt! 

Du musst diese Einrichtung **nur ein einziges Mal** durchführen.

---

### 🚀 Schritt-für-Schritt Anleitung

Um loszulegen, benötigen wir das **Terminal**. Drücke einfach `CMD + Leertaste` auf deiner Tastatur, tippe `Terminal` ein und drücke Enter.

#### Schritt 1: Homebrew installieren
Homebrew ist quasi ein inoffizieller App-Store für das Terminal. Wir brauchen es, um bestimmte Hintergrund-Werkzeuge für den Barcode-Scanner zu laden. 
Kopiere diesen Befehl ins Terminal und drücke Enter (du wirst evtl. nach deinem Mac-Passwort gefragt):

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

*(Wenn du Homebrew bereits installiert hast, überspringe diesen Schritt).*

#### Schritt 2: Python 3 und Zbar installieren
Jetzt holen wir uns die aktuelle Python-Version und `zbar` (das ist der Motor für den QR-Code-Scanner). Tippe im Terminal:

    brew install python-tk zbar

#### Schritt 3: VibeSpool herunterladen
Falls du den VibeSpool-Ordner noch nicht heruntergeladen hast, holen wir das jetzt nach. Am einfachsten geht das auch direkt im Terminal:

    cd ~/Downloads
    git clone https://github.com/SirMetalizer/VibeSpool.git
    cd VibeSpool

*(Dein Terminal befindet sich jetzt direkt im VibeSpool-Ordner).*

#### Schritt 4: Die VibeSpool-Pakete installieren
VibeSpool braucht ein paar Helferlein (für Bilder, das Netzwerk und die Kamera). Diese installieren wir jetzt mit `pip3` (dem Paketmanager von Python):

    pip3 install Pillow qrcode paho-mqtt opencv-python pyzbar

#### Schritt 5: VibeSpool starten! 🎉
Alles ist bereit! Du kannst das Programm jetzt jederzeit starten, indem du im Terminal in den VibeSpool-Ordner gehst und diesen Befehl ausführst:

    python3 filament_gui.py

---

### ⚠️ Erste Hilfe (Troubleshooting)

Macs (besonders die neueren) können manchmal etwas zickig sein, was Sicherheit und Dateipfade angeht. Hier sind die zwei häufigsten Fehler und ihre Lösungen:

**1. Pip meldet "externally-managed-environment"**
Neuere macOS-Versionen wollen verhindern, dass du globale Pakete installierst. Wenn der Befehl aus Schritt 4 rot aufleuchtet und einen Fehler wirft, hänge einfach ein `--break-system-packages` hinten an. Das ist für dieses Projekt völlig okay:

    pip3 install Pillow qrcode paho-mqtt opencv-python pyzbar --break-system-packages

**2. "Zbar library not found" (Besonders bei M1/M2/M3 Macs)**
Manchmal findet Python die Zbar-Bibliothek auf den neuen "Apple Silicon" Chips nicht sofort. Wenn VibeSpool beim Starten oder Scannen abstürzt, tippe diesen Befehl ins Terminal, *bevor* du VibeSpool startest:

    export IMAGE_LIBRARY_PATH="$(brew --prefix zbar)/lib/libzbar.dylib"

---
*Viel Spaß beim Organisieren deines Filament-Lagers auf dem Mac! 🧵✨*
