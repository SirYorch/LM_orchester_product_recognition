#!/usr/bin/env python3
"""
Script de prueba para el endpoint /chat con detección de productos.
Simula peticiones al endpoint para demostrar la funcionalidad.
"""

import requests
import json

# URL del backend (ajusta según tu configuración)
BACKEND_URL = "http://localhost:8000"  # Cambia el puerto si es necesario

def test_chat_endpoint():
    """
    Prueba el endpoint /chat con diferentes mensajes.
    """
    print("=" * 80)
    print("PRUEBA DEL ENDPOINT /chat CON DETECCIÓN DE PRODUCTOS")
    print("=" * 80)
    print()
    
    # Mensajes de prueba
    test_messages = [
        "Me gusta la Coca-Cola",
        "Hoy compré Pepsi y Sprite",
        "La Coca-Cola es mi favorita junto con la Pepsi",
        "Este mensaje no menciona ningún producto",
        "¿Tienen coca-cola disponible?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Enviando mensaje:")
        print(f"   '{message}'")
        print()
        
        try:
            # Hacer petición POST al endpoint
            response = requests.post(
                f"{BACKEND_URL}/api/chat",
                headers={"Content-Type": "application/json"},
                json={"message": message, "image": None}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("   ✓ Respuesta del servidor:")
                print(f"   {data.get('content', 'Sin contenido')}")
            else:
                print(f"   ✗ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("   ✗ Error: No se pudo conectar al servidor")
            print(f"   Asegúrate de que el servidor esté corriendo en {BACKEND_URL}")
            break
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        print()
        print("-" * 80)


def test_single_message(message):
    """
    Prueba el endpoint con un mensaje específico.
    
    Args:
        message: Mensaje a enviar
    """
    print(f"\nEnviando: '{message}'")
    print()
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            json={"message": message, "image": None}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Respuesta:")
            print(data.get('content', 'Sin contenido'))
        else:
            print(f"Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Si se pasa un mensaje como argumento
        custom_message = " ".join(sys.argv[1:])
        test_single_message(custom_message)
    else:
        # Ejecutar pruebas de ejemplo
        test_chat_endpoint()
        
        print("\n💡 Tip: Puedes probar con un mensaje personalizado:")
        print('   python3 test_chat_endpoint.py "Tu mensaje aquí"')
        print()
        print("   O inicia el servidor con:")
        print("   uvicorn main:app --reload")
