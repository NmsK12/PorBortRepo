import requests
import json

# Configuración
API_BASE_URL = "https://zgatoodni.up.railway.app/dniresult"
API_KEY = "3378f24e438baad1797c5b"
DNI_TEST = "44443333"

def test_api():
    """Probar la API de DNI"""
    url = f"{API_BASE_URL}?dni={DNI_TEST}&key={API_KEY}"
    
    print(f"Probando API con DNI: {DNI_TEST}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("API funcionando correctamente!")
            print("Datos recibidos:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Error en API: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except Exception as e:
        print(f"Error al conectar con la API: {e}")

if __name__ == "__main__":
    test_api()
