#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_dni_api():
    """Probar API de DNI"""
    print("=== PROBANDO API DNI ===")
    url = "https://zgatoodni.up.railway.app/dniresult?dni=44443333&key=3378f24e438baad1797c5b"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"JSON Data: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

def test_nombres_api():
    """Probar API de nombres"""
    print("\n=== PROBANDO API NOMBRES ===")
    url = "https://zgatoonm.up.railway.app/nm"
    params = {
        'nombres': 'PEDRO',
        'apellidos': 'CASTILLO|TERRONES',
        'key': '9d2c423573b857e46235f9c50645f'
    }
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"JSON Data: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

def test_telefono_api():
    """Probar API de teléfonos"""
    print("\n=== PROBANDO API TELEFONOS ===")
    url = "http://161.132.51.34:1520/api/osipteldb?tel=123456789"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"JSON Data: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

def test_arbol_api():
    """Probar API de árbol genealógico"""
    print("\n=== PROBANDO API ARBOL GENEALOGICO ===")
    url = "https://zgatooarg.up.railway.app/ag?dni=44443333&key=d59c297a6fd28f7e4387720e810a66b5"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"JSON Data: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_dni_api()
    test_nombres_api()
    test_telefono_api()
    test_arbol_api()
