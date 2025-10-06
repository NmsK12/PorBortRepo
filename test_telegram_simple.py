import requests
import json
import os

# Configuración
BOT_TOKEN = "7735457887:AAF-bzmviBfh5x1kuMe0IQaaP_Ij9VoBpxM"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def test_bot_info():
    """Probar información del bot"""
    print("Probando información del bot...")
    url = f"{TELEGRAM_API_URL}/getMe"
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        if result.get('ok'):
            print(f"OK - Bot funcionando: {result['result']['first_name']}")
            return True
        else:
            print(f"ERROR - Error del bot: {result}")
            return False
    except Exception as e:
        print(f"ERROR - Error de conexión: {e}")
        return False

def test_send_simple_message():
    """Probar envío de mensaje simple"""
    print("\nProbando mensaje simple...")
    
    # Usar un chat_id del log
    test_chat_id = "8079600752"
    
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {
        'chat_id': test_chat_id,
        'text': 'Prueba de mensaje simple\n\nEste es un mensaje de prueba.',
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print("OK - Mensaje simple enviado correctamente")
            return True
        else:
            print(f"ERROR - Error enviando mensaje simple: {result}")
            return False
    except Exception as e:
        print(f"ERROR - Error de conexión: {e}")
        return False

def test_send_photo():
    """Probar envío de foto"""
    print("\nProbando envío de foto...")
    
    # Verificar si existe imagen.jpg
    if not os.path.exists('imagen.jpg'):
        print("ERROR - Archivo imagen.jpg no encontrado")
        return False
    
    test_chat_id = "8079600752"
    
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    
    try:
        with open('imagen.jpg', 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': test_chat_id,
                'caption': 'Prueba de foto\n\nEsta es una prueba de envío de imagen.',
                'parse_mode': 'HTML'
            }
            
            print(f"Enviando foto a chat_id: {test_chat_id}")
            response = requests.post(url, files=files, data=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                print("OK - Foto enviada correctamente")
                return True
            else:
                print(f"ERROR - Error enviando foto: {result}")
                print(f"Status code: {response.status_code}")
                return False
    except Exception as e:
        print(f"ERROR - Error de conexión: {e}")
        return False

def test_send_photo_with_reply():
    """Probar envío de foto con reply"""
    print("\nProbando foto con reply...")
    
    if not os.path.exists('imagen.jpg'):
        print("ERROR - Archivo imagen.jpg no encontrado")
        return False
    
    test_chat_id = "8079600752"
    reply_to_message_id = 12345  # ID de prueba
    
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    
    try:
        with open('imagen.jpg', 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': test_chat_id,
                'caption': 'Prueba de foto con reply\n\nEsta es una prueba con reply_to_message_id.',
                'parse_mode': 'HTML',
                'reply_to_message_id': reply_to_message_id
            }
            
            print(f"Enviando foto con reply a chat_id: {test_chat_id}")
            response = requests.post(url, files=files, data=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                print("OK - Foto con reply enviada correctamente")
                return True
            else:
                print(f"ERROR - Error enviando foto con reply: {result}")
                print(f"Status code: {response.status_code}")
                return False
    except Exception as e:
        print(f"ERROR - Error de conexión: {e}")
        return False

def main():
    print("Iniciando pruebas de API de Telegram...")
    print(f"URL base: {TELEGRAM_API_URL}")
    
    # Ejecutar todas las pruebas
    tests = [
        test_bot_info,
        test_send_simple_message,
        test_send_photo,
        test_send_photo_with_reply
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print(f"\nResultados:")
    print(f"Exitosos: {sum(results)}")
    print(f"Fallidos: {len(results) - sum(results)}")
    
    if all(results):
        print("\nTodas las pruebas pasaron! La API funciona correctamente.")
    else:
        print("\nAlgunas pruebas fallaron. Revisa los errores arriba.")

if __name__ == "__main__":
    main()