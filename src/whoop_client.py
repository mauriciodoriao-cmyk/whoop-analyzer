import os
import requests
import datetime
import time
from dotenv import load_dotenv, set_key

load_dotenv()

CLIENT_ID = os.getenv("WHOOP_CLIENT_ID")
CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
API_BASE_URL = "https://api.prod.whoop.com/developer/v2"

class WhoopClient:
    def __init__(self):
        from src.drive_client import DriveClient
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.refresh_token = os.getenv("WHOOP_REFRESH_TOKEN")
        self.access_token = None
        self.token_expiry = 0
        
        self.drive = DriveClient()
        if self.drive.service:
            temp_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_token.txt')
            if self.drive.download_file_by_name("whoop_token.txt", temp_path):
                with open(temp_path, 'r') as f:
                    drive_token = f.read().strip()
                if drive_token:
                    self.refresh_token = drive_token
                os.remove(temp_path)

    def save_refresh_token(self, new_token):
        self.refresh_token = new_token
        # Guardar en .env local (para desarrollo)
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        set_key(env_path, "WHOOP_REFRESH_TOKEN", new_token)
        
        # Subir a Google Drive para persistencia en nube
        if hasattr(self, 'drive') and self.drive.service:
            self.drive.upload_content(new_token, "whoop_token.txt")

    def get_auth_url(self):
        import urllib.parse
        scopes = "read:recovery read:sleep read:cycles read:workout read:profile offline"
        encoded_scopes = urllib.parse.quote(scopes)
        return f"https://api.prod.whoop.com/oauth/oauth2/auth?client_id={self.client_id}&response_type=code&redirect_uri={REDIRECT_URI}&scope={encoded_scopes}&state=mauriciobot"

    def exchange_code(self, code):
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": REDIRECT_URI
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        try:
            resp = requests.post(TOKEN_URL, data=data, headers=headers, verify=False, timeout=10)
            if resp.status_code == 200:
                tokens = resp.json()
                self.access_token = tokens.get("access_token")
                self.token_expiry = time.time() + tokens.get("expires_in", 3600)
                self.save_refresh_token(tokens.get("refresh_token"))
                return True
            print(f"Error Whoop: {resp.status_code} - {resp.text}")
            return False
        except Exception as e:
            print(f"Exception en exchange_code: {str(e)}")
            return False

    def refresh_access_token(self):
        if not self.refresh_token:
            raise Exception("No hay refresh_token disponible. Se requiere autenticación.")
            
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": REDIRECT_URI,
            "scope": "offline"
        }
        resp = requests.post(TOKEN_URL, data=data, verify=False, timeout=10)
        if resp.status_code == 200:
            tokens = resp.json()
            self.access_token = tokens.get("access_token")
            self.token_expiry = time.time() + tokens.get("expires_in", 3600)
            self.save_refresh_token(tokens.get("refresh_token", self.refresh_token))
        else:
            raise Exception(f"Error refrescando el token: {resp.text}")

    def _get_headers(self):
        if not self.access_token or time.time() >= self.token_expiry - 60:
            self.refresh_access_token()
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_latest_recovery(self):
        headers = self._get_headers()
        resp = requests.get(f"{API_BASE_URL}/recovery", headers=headers, verify=False, timeout=10)
        if resp.status_code == 200 and resp.json().get('records'):
            for r in resp.json()['records']:
                if r.get('score_state') == 'SCORED':
                    return r
        return None

    def get_latest_sleep(self):
        headers = self._get_headers()
        resp = requests.get(f"{API_BASE_URL}/activity/sleep", headers=headers, verify=False, timeout=10)
        if resp.status_code == 200 and resp.json().get('records'):
            for s in resp.json()['records']:
                if s.get('score_state') == 'SCORED':
                    return s
        return None

    def get_latest_cycle(self):
        headers = self._get_headers()
        resp = requests.get(f"{API_BASE_URL}/cycle", headers=headers, verify=False, timeout=10)
        if resp.status_code == 200 and resp.json().get('records'):
            for c in resp.json()['records']:
                # Return the most recent cycle that has FINISHED (end is not null)
                if c.get('end') is not None and c.get('score_state') == 'SCORED':
                    return c
        return None

    def get_workouts_for_cycle(self, cycle_start, cycle_end):
        headers = self._get_headers()
        # Fetch latest workouts and filter them based on cycle boundaries
        resp = requests.get(f"{API_BASE_URL}/activity/workout?limit=25", headers=headers, verify=False, timeout=10)
        cycle_workouts = []
        if resp.status_code == 200 and resp.json().get('records'):
            for w in resp.json()['records']:
                w_start = w.get('start')
                w_end = w.get('end')
                # A workout belongs to a cycle if it ends before the cycle ends and starts after the cycle starts.
                # However, comparing strings directly works because ISO 8601 strings are lexicographically sortable.
                # Cycle might not have an end if it's open, but we only process FINISHED cycles.
                if w_start and w_end and cycle_start and cycle_end:
                    if w_start >= cycle_start and w_end <= cycle_end:
                        if w.get('score_state') == 'SCORED':
                            cycle_workouts.append(w)
        return cycle_workouts

