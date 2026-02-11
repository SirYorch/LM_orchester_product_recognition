#!/usr/bin/env python3
"""
Script de ejemplo para leer el archivo CSV de productos.
Este archivo muestra cómo acceder a los datos de productos registrados.
"""

import csv
import os

def read_products_csv(csv_path="products.csv"):
    """
    Lee el archivo CSV de productos y retorna una lista de diccionarios.
    
    Args:
        csv_path: Ruta al archivo CSV (por defecto: products.csv)
    
    Returns:
        Lista de diccionarios con 'product_id' y 'name'
    """
    products = []
    
    if not os.path.exists(csv_path):
        print(f"⚠️  El archivo {csv_path} no existe aún.")
        print("   Registra productos primero usando el endpoint /register")
        return products
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                'product_id': row['product_id'],
                'name': row['name']
            })
    
    return products


def get_product_by_id(product_id, csv_path="products.csv"):
    """
    Busca un producto por su ID.
    
    Args:
        product_id: ID del producto a buscar
        csv_path: Ruta al archivo CSV
    
    Returns:
        Diccionario con los datos del producto o None si no se encuentra
    """
    products = read_products_csv(csv_path)
    for product in products:
        if product['product_id'] == product_id:
            return product
    return None


def get_product_by_name(name, csv_path="products.csv"):
    """
    Busca productos por nombre (búsqueda parcial, case-insensitive).
    
    Args:
        name: Nombre o parte del nombre a buscar
        csv_path: Ruta al archivo CSV
    
    Returns:
        Lista de productos que coinciden con el nombre
    """
    products = read_products_csv(csv_path)
    matches = []
    name_lower = name.lower()
    
    for product in products:
        if name_lower in product['name'].lower():
            matches.append(product)
    
    return matches


def list_all_products(csv_path="products.csv"):
    """
    Lista todos los productos registrados.
    
    Args:
        csv_path: Ruta al archivo CSV
    """
    products = read_products_csv(csv_path)
    
    if not products:
        print("📦 No hay productos registrados.")
        return
    
    print(f"\n📦 Total de productos registrados: {len(products)}\n")
    print(f"{'ID':<40} | {'Nombre'}")
    print("-" * 80)
    
    for product in products:
        print(f"{product['product_id']:<40} | {product['name']}")


if __name__ == "__main__":
    # Ejemplo de uso
    print("=" * 80)
    print("EJEMPLO DE LECTURA DEL CSV DE PRODUCTOS")
    print("=" * 80)
    
    # Listar todos los productos
    list_all_products()
    
    # Ejemplo: Buscar por ID (reemplaza con un ID real)
    # product = get_product_by_id("12345-67890-abcde")
    # if product:
    #     print(f"\n✓ Producto encontrado: {product['name']}")
    
    # Ejemplo: Buscar por nombre
    # matches = get_product_by_name("Coca")
    # print(f"\n🔍 Productos que contienen 'Coca': {len(matches)}")
    # for match in matches:
    #     print(f"  - {match['name']} (ID: {match['product_id']})")
