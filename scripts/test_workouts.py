import sys
import requests
import json
sys.path.append('.')
from src.whoop_client import WhoopClient

client = WhoopClient()
headers = client._get_headers()
API_BASE_URL = "https://api.prod.whoop.com/developer/v2"

print("==== WORKOUTS ====")
resp = requests.get(f"{API_BASE_URL}/activity/workout", headers=headers, verify=False, timeout=10)
print(resp.status_code)
if resp.status_code == 200:
    records = resp.json().get('records', [])
    print(f"Found {len(records)} workouts.")
    if len(records) > 0:
        print(json.dumps(records[0], indent=2))
