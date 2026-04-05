# 🍏 VibeSpool auf macOS – Installations-Guide

VibeSpool sollte auf Mac laufen, erfordert aber aufgrund der Sicherheitsarchitektur von macOS eine kurze Ersteinrichtung über das Terminal. 

Du musst diese Schritte **nur ein einziges Mal** durchführen. Danach kannst du VibeSpool einfach per Doppelklick starten.

---

### 🛠️ Schritt-für-Schritt Einrichtung

Öffne dein **Terminal** (drücke `CMD + Leertaste`, tippe `Terminal` ein und drücke Enter).

#### 1. Homebrew & System-Tools
Homebrew verwaltet die Bibliotheken, die der Mac nicht von Haus aus mitbringt. Kopiere den Befehl und drücke Enter (evtl. wirst du nach deinem Mac-Passwort gefragt – beim Tippen siehst du keine Sterne, das ist normal!):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
*(Falls Homebrew bereits installiert ist, überspringe diesen Punkt).*

Installiere nun Python und den Motor für den Barcode-Scanner (`zbar`):

```bash
brew install python-tk zbar
```

#### 2. VibeSpool herunterladen & vorbereiten
Wir laden den Code direkt von GitHub in deinen Download-Ordner:

```bash
cd ~/Downloads
git clone https://github.com/SirMetalizer/VibeSpool.git
cd VibeSpool
```

#### 3. Die "Sicherheits-Blase" erstellen (Venv)
Damit VibeSpool keine anderen Programme stört, erstellen wir eine virtuelle Umgebung. Das löst auch den bekannten Fehler `externally-managed-environment`:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install Pillow qrcode paho-mqtt opencv-python pyzbar
```

---

### 🚀 VibeSpool komfortabel starten

Damit du nicht jedes Mal das Terminal öffnen musst, erstellen wir uns einen **Starter für den Schreibtisch**. Kopiere diese beiden Zeilen nacheinander ins Terminal:

```bash
echo 'cd ~/Downloads/VibeSpool && source venv/bin/activate && python3 filament_gui.py' > ~/Desktop/VibeSpool.command
chmod +x ~/Desktop/VibeSpool.command
```

**Ab sofort kannst du die Datei "VibeSpool.command" auf deinem Schreibtisch einfach doppelt anklicken, um das Programm zu öffnen!**

---

### ⚠️ Problemlösung (Troubleshooting)

**Fehler: "Zbar library not found" (Besonders bei M1/M2/M3 Chips)**
Die neuen Apple-Chips speichern Bibliotheken an einem anderen Ort. Wenn VibeSpool beim Scannen abstürzt, musst du die Starter-Datei anpassen:

1. Rechtsklick auf `VibeSpool.command` auf dem Desktop -> **Öffnen mit** -> **TextEdit**.
2. Ersetze den Inhalt durch diesen Text:

```bash
export IMAGE_LIBRARY_PATH="$(brew --prefix zbar)/lib/libzbar.dylib"
cd ~/Downloads/VibeSpool
source venv/bin/activate
python3 filament_gui.py
```

**Fehler: "App von einem nicht verifizierten Entwickler"**
Da wir die App lokal aus dem Code starten, fragt macOS beim ersten Mal nach. Gehe in deine **Systemeinstellungen -> Datenschutz & Sicherheit** und klicke unten bei VibeSpool auf **"Dennoch öffnen"**.

---
*Viel Spaß mit VibeSpool v1.9.6 auf deinem Mac! 🧵✨*