# core/bambu_sync.py
import json
import ssl
import time
import threading
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

class BambuScanner:
    def __init__(self, ip_address, access_code, serial_number):
        self.ip = ip_address
        self.access_code = access_code
        self.serial = serial_number
        self.ams_data = None
        self.connected = False
        self.client = mqtt.Client(CallbackAPIVersion.VERSION2)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.connected = True
            client.subscribe(f"device/{self.serial}/report")
            request_payload = {"pushing": {"sequence_id": "1", "command": "pushall"}}
            client.publish(f"device/{self.serial}/request", json.dumps(request_payload))

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if "print" in payload and "ams" in payload["print"]:
                ams_info = payload["print"]["ams"]
                if "ams" in ams_info and len(ams_info["ams"]) > 0:
                    all_trays = []
                    for ams_unit in ams_info["ams"]:
                        ams_id = int(ams_unit.get("id", "0"))
                        for tray in ams_unit.get("tray", []):
                            tray["ams_id"] = ams_id 
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
            start_time = time.time()
            while self.ams_data is None and (time.time() - start_time) < timeout:
                time.sleep(0.5)
            self.client.loop_stop()
            
            if self.ams_data:
                return self.parse_trays(self.ams_data)
            return None
        except:
            return None

    def parse_trays(self, trays):
        parsed = []
        for tray in trays:
            if not tray.get("tray_type") and not tray.get("tray_info_idx"):
                parsed.append({"ams": tray.get("ams_id", 0), "slot": tray.get("id"), "empty": True})
                continue
            parsed.append({
                "ams": tray.get("ams_id", 0),
                "slot": tray.get("id"),
                "empty": False,
                "material": tray.get("tray_type", "PLA"), 
                "color_hex": tray.get("tray_color", "FFFFFF"),
                "sub_brand": tray.get("tray_sub_brands", "")
            })
        return parsed


# --- NEU: DER MULTI-COLOR HINTERGRUND-MONITOR ---
class BambuBackgroundMonitor:
    def __init__(self, ip_address, access_code, serial_number, on_finish_callback):
        self.ip, self.access_code, self.serial = ip_address, access_code, serial_number
        self.on_finish_callback = on_finish_callback
        self.client = mqtt.Client(CallbackAPIVersion.VERSION2)
        self.is_running = False
        
        self.last_gcode_state = None
        self.used_trays = set()      # NEU: Ein Set sammelt ALLE benutzten Slots ohne Duplikate!
        self.predicted_weight = 0.0  

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("🤖 Bambu Auto-Sync Monitor aktiv. Lausche auf Multi-Color Events...")
            client.subscribe(f"device/{self.serial}/report")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if "print" not in payload: return
            p = payload["print"]
            
            # 1. Welcher Slot wird GERADE benutzt? Ab in den Sammelkorb!
            if "ams" in p and "tray_now" in p["ams"]:
                t_now = int(p["ams"]["tray_now"])
                if t_now != 255: # 255 ist die externe Rolle
                    self.used_trays.add(t_now)

            # 2. Geschätztes Gesamtgewicht
            if "subtask_info" in p and "weight" in p["subtask_info"]:
                self.predicted_weight = float(p["subtask_info"]["weight"])
                
            # 3. Status-Wechsel überwachen
            if "gcode_state" in p:
                new_state = p["gcode_state"]
                
                # NEU: Wir loggen jeden Statuswechsel in die Konsole!
                if self.last_gcode_state != new_state and self.last_gcode_state is not None:
                    print(f"📡 [Bambu Status] {self.last_gcode_state} ➡️ {new_state}")
                
                # NEU: Wir reagieren jetzt auf FINISH (Erfolg) UND FAILED (Abbruch)
                if self.last_gcode_state == "RUNNING" and new_state in ["FINISH", "FAILED"]:
                    print("🎯 Druck-Ende erkannt! Sende Daten an VibeSpool-Popup...")
                    if self.used_trays:
                        self.on_finish_callback(list(self.used_trays), self.predicted_weight)
                        self.used_trays.clear() # Korb leeren für den nächsten Druck
                        
                self.last_gcode_state = new_state
        except Exception as e:
            pass

    def start(self):
        if self.is_running: return
        self.is_running = True
        self.client.username_pw_set("bblp", self.access_code)
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS, cert_reqs=ssl.CERT_NONE)
        self.client.tls_insecure_set(True)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        def run_loop():
            try:
                self.client.connect(self.ip, 8883, 60)
                self.client.loop_forever()
            except: self.is_running = False
        threading.Thread(target=run_loop, daemon=True).start()

    def stop(self):
        self.is_running = False
        self.client.disconnect()
        self.client.loop_stop()