import urllib.request
import urllib.error
import json

BASE_URL = "https://evoforge.onrender.com"
ENDPOINTS = [
    "/api/status",
    "/api/runtime/status",
    "/api/runtime/pipeline-status",
    "/api/settings/compute"
]

for ep in ENDPOINTS:
    url = f"{BASE_URL}{ep}"
    print(f"--- GET {ep} ---")
    req = urllib.request.Request(url, headers={
        'User-Agent': 'EvoForgeValidator',
        'Authorization': 'Bearer default-dev-token'
    })
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(json.dumps(data, indent=2))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"HTTP Error: {e.code} - {body}")
    except Exception as e:
        print(f"Error: {e}")
    print("\n")
