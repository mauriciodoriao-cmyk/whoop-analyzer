import sys
import requests
sys.path.append('.')
from src.whoop_client import WhoopClient
import json

client = WhoopClient()
headers = client._get_headers()
API_BASE_URL = "https://api.prod.whoop.com/developer/v1"

# Get cycles
resp = requests.get(f"{API_BASE_URL}/cycle", headers=headers, verify=False, timeout=10)
cycles = resp.json().get('records', [])

if len(cycles) > 0:
    cycle = cycles[0]
    cycle_id = cycle['id']
    print("Latest Cycle:", json.dumps(cycle, indent=2))
    
    # Try recovery
    print("==== RECOVERY FOR CYCLE ====")
    resp = requests.get(f"{API_BASE_URL}/cycle/{cycle_id}/recovery", headers=headers, verify=False, timeout=10)
    print(resp.status_code, resp.text)

    # Try sleep
    print("==== SLEEP ====")
    resp = requests.get(f"{API_BASE_URL}/activity/sleep", headers=headers, verify=False, timeout=10)
    print(resp.status_code, resp.text)
