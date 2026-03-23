import json
import urllib.request

def parse_ver(v):
    """Parses a version string into a list of integers for comparison."""
    if not v: return []
    return [int(x) for x in v.lstrip("vV").replace('-', '.').split('.') if x.isdigit()]

def calculate_net_weight(gross, spool_id, spools):
    try:
        g = float(str(gross).replace(',', '.'))
        s = next((s for s in spools if s['id'] == spool_id), None)
        return max(0, int(g - (s['weight'] if s else 0)))
    except:
        return 0

def check_for_updates(github_repo, current_version):
    try:
        url = f"https://api.github.com/repos/{github_repo}/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'VibeSpool-App'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            latest_tag = data.get("tag_name", "")
            download_url = data.get("html_url", "")
            
            if download_url and parse_ver(latest_tag) > parse_ver(current_version):
                return latest_tag, download_url
    except:
        pass
    return None
