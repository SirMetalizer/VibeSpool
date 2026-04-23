import requests
import json
import webbrowser
import http.server
import socketserver
import threading
import urllib.parse

class BambuCloudAPI:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.refresh_token = None
        self.base_url = "https://api.bambulab.com/v1"
        self.server_running = False
    
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
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}: {response.text}"
                
            data = response.json()
            
            if data.get("loginType") == "verifyCode": return False, "2FA_REQUIRED"
            
            token = data.get("accessToken")
            if token:
                self.token = token
                self.refresh_token = data.get("refreshToken")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                return True, {"access": self.token, "refresh": self.refresh_token}
                
            bambu_error = data.get("message", "")
            if not bambu_error:
                bambu_error = str(data)
                
            return False, f"Bambu sagt: {bambu_error}"
            
        except Exception as e:
            return False, f"Verbindungsfehler: {str(e)}"

    def login_with_refresh(self, refresh_token):
        url = f"{self.base_url}/user-service/user/refresh" 
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

    def login_via_browser(self, callback_success):
        """Startet den OAuth-Flow über den System-Browser (Der echte Bambu Studio Link)."""
        PORT = 8080
        
        login_url = "https://bambulab.com/de-de/sign-in?from=studio&source=portal&to=https%3A%2F%2Fbambulab.com%2Fsign-in%2Fcallback%3Fsource%3Dportal%26locale%3Dde%26redirect_url%3Dhttp%253A%252F%252Flocalhost%253A8080%26openBy%3Dsuite%26from%3Dstudio"
        
        auth_result = {}
        
        class OAuthHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                
                # FIX: Wir lauschen jetzt auch auf "access_token" (mit Unterstrich)!
                if any(k in params for k in ["token", "ticket", "code", "accessToken", "access_token"]):
                    auth_result["data"] = params
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html><body style='font-family:sans-serif;text-align:center;padding-top:50px;'>")
                    self.wfile.write(b"<h1 style='color:#2ecc71;'>VibeSpool Login erfolgreich!</h1>")
                    self.wfile.write(b"<p>Du kannst dieses Fenster jetzt schliessen und zu VibeSpool zurueckkehren.</p>")
                    self.wfile.write(b"</body></html>")
                    
                    threading.Thread(target=self.server.shutdown).start()
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args): return

        def run_server():
            with socketserver.TCPServer(("localhost", PORT), OAuthHandler) as httpd:
                self.server_running = True
                httpd.handle_request() 
                
                if "data" in auth_result:
                    params = auth_result["data"]
                    # FIX: Holt den Token nun priorisiert unter "access_token"
                    token = params.get("access_token", params.get("token", params.get("ticket", params.get("accessToken", params.get("code", [None])))))[0]
                    
                    if token:
                        self.token = token
                        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                        callback_success(True, token)
                    else:
                        callback_success(False, "Kein Ticket oder Token im Redirect gefunden.")
                else:
                    callback_success(False, "Login abgebrochen.")

        webbrowser.open(login_url)
        threading.Thread(target=run_server, daemon=True).start()

    def fetch_print_history(self, limit=10):
        if not self.token: return False, "Nicht eingeloggt."
        url = f"{self.base_url}/user-service/my/tasks"
        try:
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            jobs = []
            if isinstance(data, list):
                jobs = data
            elif isinstance(data, dict):
                jobs = data.get("data", data.get("hits", data.get("tasks", [])))
                if not jobs and "data" in data and isinstance(data["data"], dict):
                     jobs = data["data"].get("hits", [])

            history_list = []
            for job in jobs[:limit]:
                weight = job.get("weight", job.get("profileWeight", job.get("filament_usage", 0)))
                name = job.get("title", job.get("designTitle", job.get("name", "Unbekannter Druck")))
                date_end = job.get("endTime", job.get("createTime", job.get("end_time", "")))

                duration_hours = 0.0
                import datetime
                try:
                    start_str = job.get("startTime", job.get("createTime", ""))
                    end_str = job.get("endTime", "")
                    if start_str and end_str:
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
                    "duration_h": duration_hours,
                    "mapping": job.get("amsDetailMapping", [])
                })
                
            return True, history_list
        except Exception as e:
            return False, str(e)