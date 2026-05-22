import sys
import time
import urllib3
sys.path.append('.')
from src.whoop_client import WhoopClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client = WhoopClient()
code = "JZjtVVF2EdetZW_mWsVF-Ofr7wnK7JEXsi9UFiCSFhA.2-uslqa7NlF5HB_RqO7GiocUhrk4Za5zM8LDdbFMpa8"

for attempt in range(2):
    print(f"Intento {attempt+1}...")
    try:
        success = client.exchange_code(code)
        if success:
            print("EXITO ABSOLUTO. Token guardado en .env.")
            sys.exit(0)
        else:
            print("Fallo en la respuesta de Whoop.")
    except Exception as e:
        print(f"Fallo de red: {e}")
    time.sleep(2)

print("FALLO TOTAL.")
sys.exit(1)
