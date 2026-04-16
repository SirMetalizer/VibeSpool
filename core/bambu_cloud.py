import requests
import json

class BambuCloudAPI:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.refresh_token = None
        self.base_url = "https://api.bambulab.com/v1"
    
    def set_auth_token(self, access_token):
        """Setzt einen bestehenden 90-Tage-Token, um den Login komplett zu überspringen."""
        self.token = access_token
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def login(self, email, password, verification_code=None):
        """Standard-Login mit Passwort und optionalem 2FA-Code."""
        url = f"{self.base_url}/user-service/user/login"
        payload = {"account": email, "password": password}
        if verification_code: payload["code"] = verification_code
        
        try:
            headers = {"User-Agent": "BambuHandy/2.0", "Content-Type": "application/json"}
            response = self.session.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("loginType") == "verifyCode": return False, "2FA_REQUIRED"
            
            token = data.get("accessToken")
            if token:
                self.token = token
                self.refresh_token = data.get("refreshToken") # Wichtig für später!
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                return True, {"access": self.token, "refresh": self.refresh_token}
            return False, data.get("message", "Login fehlgeschlagen.")
        except Exception as e:
            return False, str(e)

    def login_with_refresh(self, refresh_token):
        """Versucht den Login nur mit dem gespeicherten Refresh-Token (Kein 2FA nötig!)."""
        url = f"{self.base_url}/user-service/user/refresh" # Spezieller Endpunkt zum Erneuern
        payload = {"refreshToken": refresh_token}
        try:
            response = self.session.post(url, json=payload, timeout=10)
            data = response.json()
            token = data.get("accessToken")
            if token:
                self.token = token
                self.refresh_token = data.get("refreshToken")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                return True, {"access": self.token, "refresh": self.refresh_token}
            return False, "Token abgelaufen"
        except:
            return False, "Netzwerkfehler"

    def fetch_print_history(self, limit=10):
        if not self.token: return False, "Nicht eingeloggt."
        url = f"{self.base_url}/user-service/my/tasks"
        try:
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            # --- DEBUG LOGGING ---
            import json, os
            debug_path = os.path.join(os.getcwd(), "bambu_tasks_debug.json")
            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(f"☁️ [Bambu Tasks]: Antwort gespeichert in {debug_path}")
            # ---------------------
            
            # Hier greifen wir tiefer, da Bambu manchmal "hits" oder "tasks" als Unterordner nutzt
            jobs = []
            if isinstance(data, list):
                jobs = data
            elif isinstance(data, dict):
                # Wir durchsuchen alle bekannten Felder
                jobs = data.get("data", data.get("hits", data.get("tasks", [])))
                # Wenn es ein verschachteltes "data" -> "hits" gibt:
                if not jobs and "data" in data and isinstance(data["data"], dict):
                     jobs = data["data"].get("hits", [])

            history_list = []
            for job in jobs[:limit]:
                weight = job.get("weight", job.get("profileWeight", job.get("filament_usage", 0)))
                name = job.get("title", job.get("designTitle", job.get("name", "Unbekannter Druck")))
                date_end = job.get("endTime", job.get("createTime", job.get("end_time", "")))

                # --- NEU: Druckzeit für die Stromkosten berechnen ---
                duration_hours = 0.0
                import datetime
                try:
                    start_str = job.get("startTime", job.get("createTime", ""))
                    end_str = job.get("endTime", "")
                    if start_str and end_str:
                        # Bambu liefert Zeitstempel wie "2024-04-12T15:30:00.000Z"
                        fmt = "%Y-%m-%dT%H:%M:%S"
                        s_clean = start_str.split(".")[0].replace("Z", "")
                        e_clean = end_str.split(".")[0].replace("Z", "")
                        t_start = datetime.datetime.strptime(s_clean, fmt)
                        t_end = datetime.datetime.strptime(e_clean, fmt)
                        duration_hours = (t_end - t_start).total_seconds() / 3600.0
                except Exception: pass

                if "T" in date_end: date_end = date_end.replace("T", " ").split(".")[0]
                
                history_list.append({
                    "id": str(job.get("id", "")),
                    "name": name,
                    "weight": float(weight) if weight else 0.0,
                    "date": date_end,
                    "duration_h": duration_hours, # NEU: Wird für Stromkosten übergeben!
                    "mapping": job.get("amsDetailMapping", [])
                })
                
            return True, history_list
        except Exception as e:
            return False, str(e)