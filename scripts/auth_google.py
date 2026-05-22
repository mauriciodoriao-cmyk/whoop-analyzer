import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']

def main():
    creds = None
    base_dir = os.path.dirname(os.path.dirname(__file__))
    token_path = os.path.join(base_dir, 'token.json')
    client_secret_path = os.path.join(base_dir, 'client_secret.json')

    if not os.path.exists(client_secret_path):
        print(f"ERROR: No se encontró el archivo {client_secret_path}")
        print("Por favor descarga el archivo JSON de OAuth 2.0 desde Google Cloud y renómbralo a 'client_secret.json'")
        return

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refrescando token...")
            creds.refresh(Request())
        else:
            print("Abriendo navegador para iniciar sesión con Google...")
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            print(f"¡Éxito! Token guardado en {token_path}")
            
if __name__ == '__main__':
    main()
