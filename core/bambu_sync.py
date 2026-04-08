# core/bambu_sync.py
import json
import ssl
import time
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

class BambuScanner:
    def __init__(self, ip_address, access_code, serial_number):
        self.ip = ip_address
        self.access_code = access_code
        self.serial = serial_number # NEU: Die Seriennummer!
        self.ams_data = None
        self.connected = False
        self.client = mqtt.Client(CallbackAPIVersion.VERSION2)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.connected = True
            print("\n🔌 Verbunden! Fordere AMS-Daten aktiv vom Drucker an...")
            
            # 1. Wir abonnieren GANZ GEZIELT nur diesen einen Drucker
            client.subscribe(f"device/{self.serial}/report")
            
            # 2. Wir zwingen den Drucker, sofort einen kompletten Status-Report zu senden!
            request_payload = {"pushing": {"sequence_id": "1", "command": "pushall"}}
            client.publish(f"device/{self.serial}/request", json.dumps(request_payload))
        else:
            print(f"❌ Verbindung fehlgeschlagen! Grund: {reason_code}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            print(".", end="", flush=True) # Zeigt an, dass Daten fließen

            if "print" in payload and "ams" in payload["print"]:
                ams_info = payload["print"]["ams"]
                if "ams" in ams_info and len(ams_info["ams"]) > 0:
                    all_trays = []
                    
                    # FEHLER BEHOBEN: Wir iterieren jetzt über ALLE angeschlossenen AMS-Einheiten!
                    for ams_unit in ams_info["ams"]:
                        ams_id = int(ams_unit.get("id", "0"))
                        
                        for tray in ams_unit.get("tray", []):
                            tray["ams_id"] = ams_id  # Wir stempeln das Tray mit seiner AMS-Nummer
                            all_trays.append(tray)
                            
                    self.ams_data = all_trays
                    self.client.disconnect()
        except:
            pass

    def fetch_ams_inventory(self, timeout=10):
        self.client.username_pw_set("bblp", self.access_code)
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS, cert_reqs=ssl.CERT_NONE)
        self.client.tls_insecure_set(True)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        try:
            self.client.connect(self.ip, 8883, 60)
            self.client.loop_start()

            print(f"Suche Drucker auf {self.ip}...")
            start_time = time.time()
            
            while self.ams_data is None and (time.time() - start_time) < timeout:
                time.sleep(0.5)

            self.client.loop_stop()
            
            if self.ams_data:
                print("\n✅ AMS Daten erfolgreich empfangen!")
                return self.parse_trays(self.ams_data)
            else:
                print("\n❌ Timeout: Keine AMS Daten empfangen.")
                return None

        except Exception as e:
            print(f"\n❌ Netzwerkfehler: {e}")
            return None

    def parse_trays(self, trays):
        parsed = []
        for tray in trays:
            # Wenn weder Typ noch Info da sind, ist der Slot garantiert leer
            if not tray.get("tray_type") and not tray.get("tray_info_idx"):
                parsed.append({
                    "ams": tray.get("ams_id", 0),
                    "slot": tray.get("id"), 
                    "empty": True
                })
                continue
                
            parsed.append({
                "ams": tray.get("ams_id", 0),
                "slot": tray.get("id"),
                "empty": False,
                # FEHLER BEHOBEN: 'tray_type' enthält zuverlässig PLA, PETG, ABS, etc.
                "material": tray.get("tray_type", "PLA"), 
                "color_hex": tray.get("tray_color", "FFFFFF"),
                "sub_brand": tray.get("tray_sub_brands", "")
            })
        return parsed


if __name__ == "__main__":
    DRUCKER_IP = "192.168.XXX.XXX" 
    ACCESS_CODE = "DEIN_CODE"
    SERIENNUMMER = "DEINE_SERIE"
    
    scanner = BambuScanner(DRUCKER_IP, ACCESS_CODE, SERIENNUMMER)
    ergebnis = scanner.fetch_ams_inventory(timeout=10)
    
    if ergebnis:
        print("\n--- Dein aktuelles AMS ---")
        for slot in ergebnis:
            if slot['empty']:
                print(f"Slot {slot['slot']}: LEER")
            else:
                print(f"Slot {slot['slot']}: {slot['material']} (Farbe: #{slot['color_hex']})")