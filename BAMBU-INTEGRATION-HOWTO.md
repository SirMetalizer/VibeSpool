### 📄 BAMBU-INTEGRATION-HOWTO.md

```markdown
# 📖 Anleitung: Bambu Lab Drucker in VibeSpool integrieren

VibeSpool bietet **zwei** mächtige Wege, um mit deinem Bambu Lab Drucker zu sprechen: Den lokalen Live-Sync (für die AMS-Slot-Erkennung) und die Bambu Cloud API (für die Druck-Historie und genaue Verbrauchswerte).

---

## Weg 1: Bambu Cloud API (Für Verbrauch & Kosten)
Dies ist der wichtigste Schritt, damit VibeSpool das verbrauchte Filament am Ende eines Drucks abziehen und die Druckkosten berechnen kann.

1. Öffne VibeSpool und gehe oben rechts auf **⚙ Optionen**.
2. Wechsle in den Reiter **🤖 Drucker** und scrolle ganz nach unten.
3. Setze den Haken bei **"Cloud-Historie & Smart-Match aktivieren"** und speichere.
4. In der linken Seitenleiste von VibeSpool erscheint nun der Button **"☁️ Cloud"**. Klicke darauf.
5. Melde dich einmalig mit deinem Bambu Lab E-Mail-Account an. (Falls 2FA aktiv ist, fragt VibeSpool dich nach dem Code aus deiner E-Mail).
6. **Fertig!** VibeSpool speichert einen sicheren 90-Tage-Token. Du siehst nun deine letzten Drucke und kannst das verbrauchte Filament per Doppelklick direkt abziehen.

---

## Weg 2: Bambu AMS Live-Sync via lokales Netzwerk
Dies ist nötig, wenn VibeSpool genau wissen soll, welche Spule in welchem AMS-Slot liegt. Dies ermöglicht das "Smart-Match" Feature beim Abziehen von Cloud-Drucken. 

**So findest du deine Zugangsdaten:**
Der Drucker muss eingeschaltet und im selben WLAN/LAN wie dein PC sein. Gehe an das Display deines Druckers oder öffne Bambu Studio:

* **Drucker IP-Adresse:** Am Drucker: Gehe auf das Zahnrad (⚙️ Einstellungen) ➔ Netzwerk. Dort steht die aktuelle IP (z.B. `192.168.178.XX`).
* **Access Code (Zugangscode):** Am Drucker: Gehe auf ⚙️ Einstellungen ➔ Netzwerk. Dort findest du den Access Code. *(Hinweis: Der "Nur LAN-Modus" muss nicht zwingend aktiviert sein!)*
* **Seriennummer:** Am Drucker: Gehe auf ⚙️ Einstellungen ➔ Allgemein ➔ Geräte-Info. Die Seriennummer beginnt meist mit `00M...` oder `01S...`.

**VibeSpool Setup:**
Trage diese drei Werte in VibeSpool unter **⚙ Optionen ➔ 🤖 Drucker** ein, setze den Haken bei **"Bambu AMS Live-Sync aktivieren"** und speichere. Im Hauptmenü auf der linken Seite kannst du nun über den **"🤖 AMS"** Button deine Spulen live mit dem Drucker abgleichen!