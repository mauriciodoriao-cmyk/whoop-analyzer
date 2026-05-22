import os
import requests
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv, set_key

load_dotenv()

CLIENT_ID = os.getenv("WHOOP_CLIENT_ID")
CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"

AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

# Scopes separados por espacio
SCOPES = "read:recovery read:sleep read:cycles read:workout read:profile"

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'code' in params:
                auth_code = params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<h1>Autenticacion exitosa!</h1><p>Obteniendo tokens...</p>")
                
                # Intercambiar auth_code por tokens
                self.exchange_code_for_token(auth_code)
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Error: No se encontro auth code.")
                
            # Detener el servidor
            raise KeyboardInterrupt()

    def exchange_code_for_token(self, code):
        print("\n[+] Intercambiando código por tokens...")
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI
        }
        response = requests.post(TOKEN_URL, data=data)
        
        if response.status_code == 200:
            tokens = response.json()
            refresh_token = tokens.get("refresh_token")
            
            if refresh_token:
                # Guardar en .env
                env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
                set_key(env_path, "WHOOP_REFRESH_TOKEN", refresh_token)
                print("\n[EXCELENTE] Refresh token obtenido y guardado en .env exitosamente!")
                print("El servidor local se cerrará. Puedes continuar con el Bot.")
            else:
                print("\n[ERROR] No se recibió refresh_token en la respuesta.")
                print(tokens)
        else:
            print(f"\n[ERROR] Falló el intercambio de token: {response.status_code}")
            print(response.text)

def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: WHOOP_CLIENT_ID o WHOOP_CLIENT_SECRET no están en .env")
        return
        
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": "mauri123"
    }
    
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    print("==========================================================")
    print("1. Abre la siguiente URL en tu navegador:")
    print(url)
    print("==========================================================")
    print("\nIniciando servidor local en http://localhost:8000 esperando la redireccion...")
    
    server = HTTPServer(('localhost', 8000), OAuthHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()

if __name__ == "__main__":
    main()
