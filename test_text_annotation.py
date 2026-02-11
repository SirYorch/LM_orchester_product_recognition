#!/usr/bin/env python3
"""
Script de prueba simple para la función annotate_text_with_csv.
Implementa la función directamente para evitar problemas de importación.
"""

import csv
import os
import re


def annotate_text_with_csv(text, csv_path="products.csv", case_sensitive=False):
    """
    Anota un texto detectando nombres de productos del CSV y agregando su SKU-ID.
    
    Args:
        text: Texto a anotar
        csv_path: Ruta al archivo CSV con productos (por defecto: products.csv)
        case_sensitive: Si True, la búsqueda es sensible a mayúsculas/minúsculas
    
    Returns:
        Texto anotado con SKU-IDs
    """
    # Leer productos del CSV
    products = []
    if not os.path.exists(csv_path):
        print(f"⚠️  CSV file not found: {csv_path}")
        return text
    
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                products.append({
                    'id': row['product_id'],
                    'name': row['name']
                })
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return text
    
    if not products:
        return text
    
    # Ordenar productos por longitud de nombre (más largo primero)
    products.sort(key=lambda p: len(p['name']), reverse=True)
    
    annotated_text = text
    
    for product in products:
        product_name = product['name']
        product_id = product['id']
        
        # Crear patrón de búsqueda
        if case_sensitive:
            pattern = r'\b' + re.escape(product_name) + r'\b'
            flags = 0
        else:
            pattern = r'\b' + re.escape(product_name) + r'\b'
            flags = re.IGNORECASE
        
        # Buscar todas las ocurrencias
        matches = list(re.finditer(pattern, annotated_text, flags=flags))
        
        # Reemplazar de atrás hacia adelante
        for match in reversed(matches):
            start, end = match.span()
            matched_text = annotated_text[start:end]
            
            # Verificar si ya fue anotado
            if "(SKU:" not in annotated_text[end:end+50]:
                replacement = f"{matched_text} (SKU:{product_id})"
                annotated_text = annotated_text[:start] + replacement + annotated_text[end:]
    
    return annotated_text


def main():
    """
    Prueba la función de anotación con diferentes ejemplos de texto.
    """
    print("=" * 80)
    print("PRUEBA DE ANOTACIÓN DE TEXTO CON SKU-IDs")
    print("=" * 80)
    print()
    
    csv_path = "products.csv"
    
    if not os.path.exists(csv_path):
        print("⚠️  No se encontró products.csv")
        return
    
    # Mostrar productos en el CSV
    print("📦 Productos registrados en CSV:\n")
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(f"   - {row['name']} (ID: {row['product_id']})")
    print()
    print("-" * 80)
    print()
    
    # Ejemplos de texto para anotar
    test_texts = [
        "Me gusta la Coca-Cola y la Pepsi",
        "Hoy compré una coca-cola en la tienda",
        "Los productos disponibles son Coca-Cola, Pepsi y Sprite",
        "La Coca-Cola es refrescante",
        "No hay productos mencionados aquí"
    ]
    
    print("📝 Textos de prueba:\n")
    
    for i, text in enumerate(test_texts, 1):
        print(f"{i}. Original:")
        print(f"   {text}")
        print()
        
        annotated = annotate_text_with_csv(text, csv_path)
        
        print(f"   Anotado:")
        print(f"   {annotated}")
        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
