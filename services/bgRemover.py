#!/usr/bin/env python3
"""
bgRemover: Una aplicación para remover fondos de imágenes impresion*.jpeg
"""

import glob
import os
import io
import logging
import numpy as np
from rembg import remove
from PIL import Image
from logging_config import get_logger

logger = get_logger(__name__)

def process_image_bytes(image_bytes: bytes) -> bytes:
    """
    Remueve el fondo de una imagen en bytes y retorna la imagen en bytes (PNG).
    """
    logger.debug(f"Processing image bytes, size: {len(image_bytes)} bytes")
    try:
        input_image = Image.open(io.BytesIO(image_bytes))
        logger.debug(f"Image opened successfully, format: {input_image.format}, size: {input_image.size}")
        
        logger.debug("Removing background using rembg")
        output_image = remove(input_image)
        logger.debug(f"Background removed successfully, output size: {output_image.size}")
        
        logger.debug("Encoding output image as PNG")
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format='PNG')
        result_bytes = img_byte_arr.getvalue()
        
        logger.info(f"Image processing completed successfully, output size: {len(result_bytes)} bytes")
        return result_bytes
    except Exception as e:
        logger.error(f"Error processing image bytes: {str(e)}")
        raise

def remove_background(image_path, output_path):
    """
    Remueve el fondo de una imagen usando rembg.
    """
    logger.info(f"Processing image: {image_path}")
    try:
        logger.debug(f"Opening image from path: {image_path}")
        input_image = Image.open(image_path)
        logger.debug(f"Image opened successfully, size: {input_image.size}")
        
        logger.debug("Removing background")
        output_image = remove(input_image)
        logger.debug("Background removed successfully")
        
        logger.debug(f"Saving output to: {output_path}")
        output_image.save(output_path, format='PNG')
        logger.info(f"Image processed successfully: {image_path} -> {output_path}")
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")

def main():
    logger.info("Background removal script started")
    image_files = glob.glob("imr*.jpeg")
    
    if not image_files:
        logger.warning("No images found matching pattern 'imr*.jpeg'")
        return
    
    logger.info(f"Found {len(image_files)} images to process")
    
    for idx, image_file in enumerate(image_files, 1):
        logger.debug(f"Processing image {idx}/{len(image_files)}: {image_file}")
        base_name = os.path.splitext(image_file)[0]
        output_file = f"{base_name}_no_bg.png"
        
        remove_background(image_file, output_file)
    
    logger.info("Background removal script completed successfully")

if __name__ == "__main__":
    main()