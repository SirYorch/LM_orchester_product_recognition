#!/usr/bin/env python3
"""
bgRemover: Una aplicación para remover fondos de imágenes impresion*.jpeg
"""

import glob
import os
import io
import numpy as np
from rembg import remove
from PIL import Image

def process_image_bytes(image_bytes: bytes) -> bytes:
    """
    Remueve el fondo de una imagen en bytes y retorna la imagen en bytes (PNG).
    """
    input_image = Image.open(io.BytesIO(image_bytes))
    output_image = remove(input_image)
    
    img_byte_arr = io.BytesIO()
    output_image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

def remove_background(image_path, output_path):
    """
    Remueve el fondo de una imagen usando rembg.
    """
    try:
        # Abrir la imagen
        input_image = Image.open(image_path)
        
        # Remover el fondo
        output_image = remove(input_image)
        
        # Guardar la imagen resultante
        output_image.save(output_path, format='PNG')
        print(f"Fondo removido: {image_path} -> {output_path}")
    except Exception as e:
        print(f"Error procesando {image_path}: {e}")

def main():
    # Encontrar todas las imágenes que coincidan con el patrón
    image_files = glob.glob("imr*.jpeg")
    
    if not image_files:
        print("No se encontraron imágenes con el patrón 'impresion*.jpeg'")
        return
    
    print(f"Encontradas {len(image_files)} imágenes para procesar.")
    
    # Procesar cada imagen
    for image_file in image_files:
        # Crear el nombre del archivo de salida
        base_name = os.path.splitext(image_file)[0]
        output_file = f"{base_name}_no_bg.png"
        
        # Remover el fondo
        remove_background(image_file, output_file)
    
    print("Procesamiento completado.")

if __name__ == "__main__":
    main()