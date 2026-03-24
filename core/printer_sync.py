import urllib.request
import json
import logging

def fetch_recent_jobs(printer_url, api_key=None, limit=10):
    """
    Fetches a list of recent print jobs from Moonraker.
    Returns: list of dicts (job info) or None on failure.
    """
    if not printer_url: return None
    url = printer_url.strip().rstrip("/")
    if not url.startswith("http"): url = "http://" + url
    
    endpoint = f"{url}/printer/history/list?limit={limit}&order=desc"
    
    try:
        req = urllib.request.Request(endpoint)
        if api_key: req.add_header("X-Api-Key", api_key)
            
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if "result" in data and "jobs" in data["result"]:
                return data["result"]["jobs"]
    except Exception as e:
        logging.error(f"Failed to fetch printer jobs: {e}")
        return None
    return None

def fetch_last_print_usage(printer_url, api_key=None):
    """Legacy wrapper for single job fetch."""
    jobs = fetch_recent_jobs(printer_url, api_key, limit=1)
    if jobs and len(jobs) > 0:
        return jobs[0].get("filament_used", 0.0)
    return None
