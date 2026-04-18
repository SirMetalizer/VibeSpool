import http.server
import socket
import threading
import json
import re
from urllib.parse import urlparse, parse_qs

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
        s.close()
        return IP
    except: return '127.0.0.1'


MOBILE_HTML = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>VibeSpool Scanner</title>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script src="https://cdn.jsdelivr.net/npm/tesseract.js@4/dist/tesseract.min.js"></script>
    <style>
        body { background-color: #2b2b2b; color: white; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 0; }
        .header { background: #1e1e1e; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }
        h1 { font-size: 22px; margin: 0; color: #0078d7; }

        .tabs { display: flex; background: #3c3f41; }
        .tab-btn { flex: 1; padding: 15px; background: none; border: none; color: #bbb; font-size: 15px; font-weight: bold; cursor: pointer; border-bottom: 3px solid transparent; }
        .tab-btn.active { color: white; border-bottom: 3px solid #0078d7; }

        .content { padding: 20px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .btn-scan { display: inline-block; background-color: #0078d7; color: white; font-size: 18px; font-weight: bold; padding: 15px 30px; border-radius: 12px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.3); width: 100%; box-sizing: border-box;}
        .btn-scan:active { background-color: #005a9e; }
        input[type="file"] { display: none; }
        
        #status { margin-bottom: 20px; padding: 15px; border-radius: 8px; background: #3c3f41; font-weight: bold; display:none;}
        .success { background: #28a745 !important; color: white; } .error { background: #d9534f !important; color: white;}

        #dashboard { display: none; margin-top: 10px; background: #3c3f41; padding: 15px; border-radius: 10px; text-align: left;}
        #dash-title { color: #0078d7; font-size: 18px; margin-top: 0; margin-bottom: 5px; font-weight: bold;}
        #dash-net { font-size: 14px; color: #bbb; margin-bottom: 15px; }
        .control-group { margin-bottom: 15px; display: flex; gap: 10px; }
        .control-group input, .control-group select { flex-grow: 1; padding: 12px; font-size: 16px; border-radius: 5px; border: 1px solid #555; background: #2b2b2b; color: white; }
        .btn-action { padding: 12px 15px; font-size: 16px; font-weight: bold; border: none; border-radius: 5px; color: white; cursor: pointer; }
        .btn-red { background: #d9534f; } .btn-green { background: #28a745; }
        #btn-reset { width: 100%; padding: 15px; background: #555; color: white; font-size: 18px; font-weight: bold; border: none; border-radius: 8px; margin-top: 10px; cursor: pointer; }

        .instruction-box { background: #3c3f41; padding: 20px; border-radius: 10px; text-align: left; line-height: 1.6; margin-bottom: 20px; border-left: 4px solid #0078d7;}
        .instruction-box ol { padding-left: 20px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1 id="main-title">📱 VibeSpool Scanner</h1>
    </div>

    <div class="tabs" id="tab-container">
        <button class="tab-btn active" id="btn-tab-scan" onclick="switchTab('scan')">🔍 Suchen & Umbuchen</button>
        <button class="tab-btn" id="btn-tab-new" onclick="switchTab('new')">➕ Neu anlegen</button>
    </div>

    <div class="content">
        <div id="status">Bereit. Mach ein Foto oder gib eine ID ein!</div>

        <div id="tab-scan" class="tab-content active">
            <label class="btn-scan" id="scan-trigger-1">
                📷 Etikett scannen
                <input type="file" class="qr-input-file" accept="image/*" capture="environment">
            </label>

            <div id="manual-search-box" style="margin-top: 20px; background: #3c3f41; padding: 15px; border-radius: 10px;">
                <p style="margin-top: 0; color: #bbb; font-weight:bold;">Oder ID / Code manuell eingeben:</p>
                <div class="control-group">
                    <input type="text" id="manual-id" placeholder="z.B. A134 oder 401234...">
                    <button class="btn-action btn-green" onclick="searchManual()">Suchen</button>
                </div>
            </div>
        </div>

        <div id="tab-new" class="tab-content">
            <div class="instruction-box">
                <strong style="color:white; font-size: 18px;">Hersteller-Barcode eintragen:</strong>
                <ol style="color:#ddd;">
                    <li>Klicke am PC in VibeSpool auf <strong style="color:white;">Neu Hinzufügen</strong> (oder auf eine Spule).</li>
                    <li>Scanne oder tippe hier den Strichcode der Originalverpackung ein.</li>
                </ol>
                <p style="color:#28a745; font-weight:bold; margin-bottom:0;">👉 VibeSpool tippt den Code dann magisch am PC für dich ein!</p>
            </div>

            <label class="btn-scan" id="scan-trigger-2" style="background-color: #28a745;">
                📷 Barcode scannen
                <input type="file" class="qr-input-file" accept="image/*" capture="environment">
            </label>

            <div id="manual-barcode-box" style="margin-top: 20px; background: #3c3f41; padding: 15px; border-radius: 10px;">
                <p style="margin-top: 0; color: #bbb; font-weight:bold;">Code manuell abtippen:</p>
                <div class="control-group">
                    <input type="text" id="manual-barcode" placeholder="z.B. 69532145...">
                    <button class="btn-action btn-green" onclick="submitManualBarcode()">Senden</button>
                </div>
            </div>
        </div>

        <div id="dashboard">
            <h3 id="dash-title">Spule</h3>
            <div id="dash-net">Rest: 0g</div>
            <input type="hidden" id="current-id">

            <div class="control-group">
                <input type="number" id="val-usage" placeholder="Verbrauch (z.B. 140)">
                <button class="btn-action btn-red" onclick="sendAction('usage')">Abziehen</button>
            </div>

            <div class="control-group">
                <select id="val-loc"></select>
                <button class="btn-action btn-green" onclick="sendAction('move')">Umbuchen</button>
            </div>

            <button id="btn-reset" onclick="resetUI()">Fertig / Nächste Spule</button>
        </div>
        
        <div id="reader-hidden" style="display:none;"></div>
    </div>

    <script>
        const fileInputs = document.querySelectorAll('.qr-input-file');
        const statusDiv = document.getElementById("status");
        let currentTab = 'scan';

        function switchTab(tabId) {
            currentTab = tabId;
            document.getElementById('tab-scan').classList.remove('active');
            document.getElementById('tab-new').classList.remove('active');
            document.getElementById('btn-tab-scan').classList.remove('active');
            document.getElementById('btn-tab-new').classList.remove('active');

            document.getElementById('tab-' + tabId).classList.add('active');
            document.getElementById('btn-tab-' + tabId).classList.add('active');
            
            // NEU: Status ausblenden, wenn man den Tab wechselt (Bugfix)
            statusDiv.style.display = 'none';
            statusDiv.className = "";
            statusDiv.innerText = "";

            if(document.getElementById('dashboard').style.display === 'block') {
                resetUI();
            }
        }

        function resetUI() {
            document.getElementById('dashboard').style.display = 'none';
            document.getElementById('tab-' + currentTab).style.display = 'block';
            document.getElementById('tab-container').style.display = 'flex';
            statusDiv.style.display = 'none';
            statusDiv.className = "";
            document.getElementById('manual-id').value = "";
            document.getElementById('manual-barcode').value = ""; // Feld leeren
        }

        function fetchDataFromServer(scanCode) {
            statusDiv.style.display = 'block';
            statusDiv.innerText = "Sende Anfrage an PC...";
            statusDiv.className = "";

            fetch('/scan?code=' + encodeURIComponent(scanCode))
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'ok') {
                        document.getElementById('tab-scan').style.display = 'none';
                        document.getElementById('tab-new').style.display = 'none';
                        document.getElementById('tab-container').style.display = 'none';
                        statusDiv.style.display = 'none';

                        document.getElementById('dashboard').style.display = 'block';
                        document.getElementById('dash-title').innerText = data.name;
                        document.getElementById('dash-net').innerText = "Aktueller Rest: " + data.net + " g";
                        document.getElementById('current-id').value = data.id;

                        let select = document.getElementById('val-loc');
                        select.innerHTML = '<option value="">-- Neuen Ort wählen --</option>';
                        data.locs.forEach(l => {
                            select.innerHTML += `<option value="${l.val}">${l.label}</option>`;
                        });
                    } else if (data.status === 'inserted') {
                        statusDiv.innerText = data.msg;
                        statusDiv.className = "success";
                        setTimeout(resetUI, 3000);
                    } else {
                        statusDiv.innerText = "Fehler: " + data.msg;
                        statusDiv.className = "error";
                    }
                }).catch(err => {
                    statusDiv.innerText = "Netzwerkfehler zum PC.";
                    statusDiv.className = "error";
                });
        }

        function searchManual() {
            const val = document.getElementById('manual-id').value.trim();
            if(!val) return alert("Bitte eine ID eingeben!");
            fetchDataFromServer(val);
        }

        // NEU: Funktion für das Absenden des manuellen Barcodes
        function submitManualBarcode() {
            const val = document.getElementById('manual-barcode').value.trim();
            if(!val) return alert("Bitte einen Barcode eingeben!");
            fetchDataFromServer(val);
        }

        function sendAction(actionType) {
            let id = document.getElementById('current-id').value;
            let val = "";

            if (actionType === 'usage') {
                val = document.getElementById('val-usage').value;
                if (!val) return alert("Bitte Gewicht eingeben!");
            } else if (actionType === 'move') {
                val = document.getElementById('val-loc').value;
                if (!val) return;
            }

            fetch(`/action?id=${id}&action=${actionType}&val=${encodeURIComponent(val)}`)
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'ok') {
                        alert("✅ Erfolgreich gespeichert!");
                        if (actionType === 'usage') document.getElementById('val-usage').value = '';
                    } else {
                        alert("⚠️ Aktion abgelehnt:\\n" + data.msg);
                    }
                });
        }

        async function performOCR(imageCanvas) {
            statusDiv.style.display = 'block';
            statusDiv.innerText = "Kein Barcode erkannt. Prüfe auf gedruckten Text (OCR)...";
            try {
                const result = await Tesseract.recognize(imageCanvas, 'deu+eng', {
                    logger: m => { if(m.status === 'recognizing') statusDiv.innerText = `OCR Analyse: ${Math.round(m.progress * 100)}%`; }
                });

                const fullText = result.data.text;
                const match = fullText.match(/(?:VibeSpool\\s*(?:ID|1D|lD|I0)?|\\b(?:ID|1D|lD|I0))\\s*[:=_\\-\\.]*\\s*([a-zA-Z0-9-]+)/i);

                if (match && match[1]) {
                    const foundId = match[1].trim();
                    statusDiv.innerText = `Text erkannt: ID ${foundId} - Lade Daten...`;
                    fetchDataFromServer(foundId);
                } else {
                    statusDiv.innerHTML = "Kein Strichcode/QR oder VibeSpool-Text gefunden.<br><br><b>Kamera las:</b><br><i style='font-size: 12px;'>" + fullText + "</i>";
                    statusDiv.className = "error";
                }
            } catch (e) {
                statusDiv.innerText = "Fehler bei der Texterkennung.";
                statusDiv.className = "error";
            }
        }

        const html5QrCode = new Html5Qrcode("reader-hidden");

        fileInputs.forEach(input => {
            input.addEventListener('change', e => {
                if (e.target.files.length == 0) return;
                const file = e.target.files[0];
                statusDiv.style.display = 'block';
                statusDiv.innerText = "Bild wird analysiert (Suche Strichcode / QR)..."; 
                statusDiv.className = "";

                html5QrCode.scanFile(file, true)
                    .then(decodedText => {
                        statusDiv.innerText = `Code erkannt! (${decodedText})`;
                        statusDiv.className = "success";
                        fetchDataFromServer(decodedText);
                    })
                    .catch(err => {
                        const reader = new FileReader();
                        reader.onload = function(event) {
                            const img = new Image();
                            img.onload = function() {
                                const canvas = document.createElement('canvas');
                                let w = img.width, h = img.height;
                                if (w > h && w > 800) { h *= 800/w; w = 800; }
                                else if (h > 800) { w *= 800/h; h = 800; }
                                canvas.width = w; canvas.height = h;
                                const ctx = canvas.getContext('2d');
                                ctx.drawImage(img, 0, 0, w, h);
                                performOCR(canvas);
                            };
                            img.src = event.target.result;
                        };
                        reader.readAsDataURL(file);
                    });
                    
                e.target.value = ''; 
            });
        });
    </script>
</body>
</html>
"""

class MobileScannerHandler(http.server.SimpleHTTPRequestHandler):
    # Unterdrückt die nervigen Konsolen-Logs im Hintergrund
    def log_message(self, format, *args):
        pass 

    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            
            # 1. Ignoriere automatische Browser-Anfragen nach Icons sofort!
            if parsed_path.path == '/favicon.ico':
                self.send_response(204)
                self.end_headers()
                return
            
            if parsed_path.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(MOBILE_HTML.encode('utf-8'))
                
            elif parsed_path.path == '/scan':
                query = parse_qs(parsed_path.query)
                code = query.get('code', [''])[0]
                app_inst = getattr(self.server, 'app_instance', None)
                
                response_data = {"status": "error", "msg": "Spule nicht in der Datenbank."}
                
                if code and app_inst:
                    clean_code = code.strip()
                    item = None
                    
                    # 1. Prio: Exakter Treffer im neuen Hersteller-Barcode Feld!
                    item = next((i for i in app_inst.inventory if str(i.get('barcode', '')).strip().lower() == clean_code.lower() and clean_code != ""), None)
                    
                    # 2. Prio: Reguläre VibeSpool ID Suche (als Text, nicht mehr als int!)
                    if not item:
                        match = re.search(r'(?:ID|1D|lD|VibeSpool)[\s:=_\-\.]*([a-zA-Z0-9-]+)', clean_code, re.IGNORECASE)
                        extracted_id = match.group(1) if match else clean_code
                        item = next((i for i in app_inst.inventory if str(i.get('id')) == str(extracted_id)), None)
                    
                    if item:
                        spool_id = item['id']
                        app_inst.root.after(0, lambda: app_inst.process_mobile_scan(code))
                        
                        locs = [
                            {"label": "📦 Ins LAGER", "val": "LAGER|-"}, 
                            {"label": "🚮 Als LEER markieren", "val": "VERBRAUCHT|-"}
                        ]
                        
                        from core.logic import parse_shelves_string, calculate_net_weight
                        parsed_shelves = parse_shelves_string(app_inst.settings.get("shelves", "REGAL|4|8"))
                        lbl_r = app_inst.settings.get("label_row", "Fach")
                        lbl_c = app_inst.settings.get("label_col", "Slot")
                        all_names = app_inst.settings.get("shelf_names_v2", {})
                        is_double = app_inst.settings.get("double_depth", False)
                        
                        for sh in parsed_shelves:
                            name = sh['name']
                            s_names = all_names.get(name, {})
                            for r in range(1, sh['rows'] + 1):
                                row_n = s_names.get(str(r), f"{lbl_r} {r}")
                                for c in range(1, sh['cols'] + 1):
                                    if is_double:
                                        locs.append({"label": f"{name} {row_n} - {lbl_c} {c} (V)", "val": f"{name}|{row_n} - {lbl_c} {c} (V)"})
                                        locs.append({"label": f"{name} {row_n} - {lbl_c} {c} (H)", "val": f"{name}|{row_n} - {lbl_c} {c} (H)"})
                                    else:
                                        locs.append({"label": f"{name} {row_n} - {lbl_c} {c}", "val": f"{name}|{row_n} - {lbl_c} {c}"})
                                        
                        for a in range(1, app_inst.settings.get("num_ams", 1) + 1):
                            for s in range(1, 5):
                                locs.append({"label": f"AMS {a} Slot {s}", "val": f"AMS {a}|{s}"})
                                
                        net_w = calculate_net_weight(item.get('weight_gross', '0'), item.get('spool_id', -1), app_inst.spools, item.get('empty_weight'))
                        
                        response_data = {
                            "status": "ok",
                            "id": spool_id,
                            "name": f"{item.get('brand','')} {item.get('material','')} {item.get('color','')}",
                            "net": int(net_w),
                            "locs": locs
                        }
                    else:
                        # NEU: Spule nicht gefunden? Dann schick den Code ins Barcode-Feld am PC!
                        app_inst.root.after(0, lambda: app_inst.process_unknown_scan(clean_code))
                        response_data = {
                            "status": "inserted",
                            "msg": f"✅ Barcode erfolgreich am PC eingetragen!\n\n[{clean_code}]"
                        }

                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
            elif parsed_path.path == '/action':
                query = parse_qs(parsed_path.query)
                spool_id = query.get('id', [''])[0]
                action = query.get('action', [''])[0]
                val = query.get('val', [''])[0]
                
                app_inst = getattr(self.server, 'app_instance', None)
                response_data = {"status": "error", "msg": "Unbekannter Fehler"}
                
                if app_inst and spool_id and action:
                    spool_id_str = str(spool_id) 
                    if action == "move" and "|" in val:
                        target_type, target_loc = val.split("|", 1)
                        col = app_inst.check_location_collision(target_type, target_loc, ignore_id=spool_id_str)
                        
                        if col and target_type.startswith("AMS"):
                            # --- FIX 3: MOBILE QUICK SWAP ---
                            app_inst.root.after(0, lambda: app_inst.process_mobile_swap(spool_id_str, target_type, target_loc, col))
                            response_data = {"status": "ok"}
                        elif col:
                            response_data = {
                                "status": "error", 
                                "msg": f"Der Platz ist bereits belegt durch:\n#{col['id']} {col.get('brand','')} {col.get('color','')}"
                            }
                        else:
                            app_inst.root.after(0, lambda: app_inst.process_mobile_action(spool_id_str, action, val))
                            response_data = {"status": "ok"}
                    else:
                        app_inst.root.after(0, lambda: app_inst.process_mobile_action(spool_id_str, action, val))
                        response_data = {"status": "ok"}
                        
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
        except Exception as e:
            # --- DIE LEBENSRETTUNG ---
            # Statt sang- und klanglos abzustürzen, fangen wir JEDEN Fehler ab!
            print(f"Webserver Fehler abgefangen: {e}")
            try:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f"VibeSpool Server Fehler: {e}".encode('utf-8'))
            except:
                pass

def start_mobile_server(app_inst):
    port = 8289  # Neuer, freier Port!
    handler = MobileScannerHandler
    try:
        # Erlaubt den sofortigen Neustart des Servers ohne Blockade
        http.server.ThreadingHTTPServer.allow_reuse_address = True
        
        # Ein Threading-Server stürzt nicht ab, wenn das Handy etwas Falsches funkt
        httpd = http.server.ThreadingHTTPServer(("", port), handler)
        setattr(httpd, 'app_instance', app_inst) 
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
    except Exception as e:
        print(f"Webserver konnte nicht starten: {e}")