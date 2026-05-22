import sys
import requests
import json
sys.path.append('.')
from src.whoop_client import WhoopClient

client = WhoopClient()
headers = client._get_headers()

print("==== V2 CYCLES ====")
resp = requests.get("https://api.prod.whoop.com/developer/v2/cycle", headers=headers, verify=False, timeout=10)
print(resp.status_code)
if resp.status_code == 200:
    cycle_id = resp.json().get('records', [])[0]['id']
    print(f"Cycle ID: {cycle_id}")

print("\n==== V2 RECOVERY COLLECTION ====")
resp = requests.get("https://api.prod.whoop.com/developer/v2/recovery", headers=headers, verify=False, timeout=10)
print(resp.status_code)
if resp.status_code == 200:
    print(json.dumps(resp.json()['records'][0], indent=2))

print("\n==== V2 SLEEP COLLECTION ====")
resp = requests.get("https://api.prod.whoop.com/developer/v2/activity/sleep", headers=headers, verify=False, timeout=10)
print(resp.status_code)
if resp.status_code == 200:
    print(json.dumps(resp.json()['records'][0], indent=2))

