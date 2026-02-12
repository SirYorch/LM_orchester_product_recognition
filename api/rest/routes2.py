import base64
import os
import shutil
import uuid
import logging
import traceback
from typing import List, Optional

import cv2
import mlflow
import numpy as np
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from mlflow.entities import ViewType
from pydantic import BaseModel

from ml.models.sift_engine import get_sift_engine
from services.bgRemover import process_image_bytes
from services.video_service import process_video, annotate_text_with_csv
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

SIFT_STORAGE = "sift_data.pkl"

logger.debug("Initializing SIFT engine")
sift_engine = get_sift_engine(str(SIFT_STORAGE))
logger.info("SIFT engine initialized successfully")

def find_optimal_threshold(cv_image, cv_mask, target_points=1500, tolerance=50):
    """
    Encuentra el threshold optimo para obtener ~target_points keypoints.
    Retorna (best_threshold, best_vis_image, best_count).
    """
    logger.debug(f"Finding optimal threshold, target_points={target_points}")
    low = 0.001
    high = 0.2
    best_vis = None
    best_count = -1
    best_th = 0.04
    
    for iteration in range(8):
        mid = (low + high) / 2
        vis_img, count = sift_engine.detect_keypoints_vis(cv_image, mask=cv_mask, contrast_threshold=mid)
        logger.debug(f"Threshold iteration {iteration}: mid={mid:.4f}, count={count}")
        
        if best_vis is None or abs(count - target_points) < abs(best_count - target_points):
            best_vis = vis_img
            best_count = count
            best_th = mid
        
        if abs(count - target_points) <= tolerance:
            logger.debug(f"Optimal threshold found: {best_th:.4f} with {best_count} keypoints")
            break
            
        if count < target_points:
            high = mid
        else:
            low = mid
    
    logger.info(f"Optimal threshold calculation completed: threshold={best_th:.4f}, keypoints={best_count}")        
    return best_th, best_vis, best_count


@router.post('/register')
async def register(
    image: UploadFile = File(...),
    name: str = Form("Unknown")
):
    """
    Registra un producto en la base de datos.
    Elimina automáticamente el fondo de la imagen usando bgRemover.
    Calcula automáticamente el threshold para ~1500 keypoints.
    
    Espera: 'image' file, 'name' text.
    """
    logger.info(f"Product registration started for product: {name}")
    try:
        logger.debug(f"Reading image from upload - filename: {image.filename}")
        input_bytes = await image.read()
        logger.debug(f"Image read successfully, size: {len(input_bytes)} bytes")
        
        logger.debug("Processing image to remove background")
        processed_bytes = process_image_bytes(input_bytes)
        logger.debug(f"Background removed, processed size: {len(processed_bytes)} bytes")

        logger.debug("Decoding processed image")
        nparr = np.frombuffer(processed_bytes, np.uint8)
        cv_image_rgba = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
        if cv_image_rgba is None:
            logger.error("Failed to decode processed image")
            return JSONResponse(status_code=400, content={'error': 'Could not process image'})
        
        logger.debug(f"Image decoded successfully, shape: {cv_image_rgba.shape}")
        
        if cv_image_rgba.shape[2] == 4:
            cv_image = cv2.cvtColor(cv_image_rgba, cv2.COLOR_BGRA2BGR)
            cv_mask = cv_image_rgba[:, :, 3]
            logger.debug("Image has alpha channel, mask extracted")
        else:
            cv_image = cv_image_rgba
            cv_mask = None
            logger.debug("Image does not have alpha channel")

        if cv_mask is not None:
            _, cv_mask = cv2.threshold(cv_mask, 127, 255, cv2.THRESH_BINARY)
            logger.debug("Mask thresholded successfully")
        
        logger.debug("Calculating optimal threshold")
        optimal_threshold, _, keypoint_count = find_optimal_threshold(cv_image, cv_mask)
        logger.info(f"Optimal threshold calculated: {optimal_threshold}, keypoints: {keypoint_count}")

        product_id = str(uuid.uuid4())
        logger.debug(f"Generated product ID: {product_id}")

        logger.debug("Registering product in SIFT engine")
        success, msg = sift_engine.register_product(name, product_id, cv_image, mask=cv_mask, contrast_threshold=optimal_threshold)
        
        if success:
            logger.info(f"Product registered successfully - ID: {product_id}, Name: {name}")
            return JSONResponse(status_code=200, content={'message': msg, 'threshold': optimal_threshold, 'product_id': product_id})
        else:
            logger.error(f"Product registration failed - ID: {product_id}, Error: {msg}")
            return JSONResponse(status_code=500, content={'error': msg})

    except Exception as e:
        logger.error(f"Exception during product registration: {str(e)}")
        logger.debug(traceback.format_exc())
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post('/preview_keypoints')
async def preview_keypoints(
    image: UploadFile = File(...)
):
    """
    Previsualización automática:
    1. Removedor de fondo.
    2. Ajuste automático de threshold para ~1500 keypoints.
    """
    logger.info("Keypoint preview requested")
    try:
        logger.debug(f"Reading image from upload - filename: {image.filename}")
        input_bytes = await image.read()
        
        logger.debug("Processing image to remove background")
        processed_bytes = process_image_bytes(input_bytes)
        
        logger.debug("Decoding processed image")
        nparr = np.frombuffer(processed_bytes, np.uint8)
        cv_image_rgba = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
        if cv_image_rgba is None:
            logger.error("Failed to decode processed image")
            return JSONResponse(status_code=400, content={'error': 'Could not process image'})
        
        logger.debug(f"Image decoded successfully, shape: {cv_image_rgba.shape}")
            
        if cv_image_rgba.shape[2] == 4:
            cv_image = cv2.cvtColor(cv_image_rgba, cv2.COLOR_BGRA2BGR)
            cv_mask = cv_image_rgba[:, :, 3]
        else:
            cv_image = cv_image_rgba
            cv_mask = None

        if cv_mask is not None:
            _, cv_mask = cv2.threshold(cv_mask, 127, 255, cv2.THRESH_BINARY)
             
        logger.debug("Calculating optimal threshold")
        best_th, best_vis, best_count = find_optimal_threshold(cv_image, cv_mask)
        logger.info(f"Keypoint preview completed - threshold: {best_th:.4f}, count: {best_count}")
        
        _, buffer = cv2.imencode('.jpg', best_vis)
        vis_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            'keypoint_image': vis_base64,
            'count': best_count,
            'optimized_threshold': round(best_th, 5)
        }
    except Exception as e:
        logger.error(f"Exception during keypoint preview: {str(e)}")
        logger.debug(traceback.format_exc())
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post('/predict')
async def predict(image: UploadFile = File(...)):
    """
    Identificación de producto en la imagen subida.
    """
    logger.info("Product prediction requested")
    try:
        logger.debug(f"Reading image from upload - filename: {image.filename}")
        img_bytes = await image.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if cv_image is None:
            logger.error("Failed to decode image for prediction")
            return JSONResponse(status_code=400, content={'error': 'Invalid image'})

        logger.debug("Identifying product using SIFT engine")
        product_match, matches = sift_engine.identify_product(cv_image)
        
        if product_match:
            logger.info(f"Product identified - name: {product_match['name']}, id: {product_match['id']}, matches: {matches}")
            return {
                'label': product_match['name'],
                'product_id': product_match['id'],
                'matches': matches,
                'probability': 1.0
            }
        else:
            logger.warning(f"No product identified, matches: {matches}")
            return {
                'label': 'Unknown',
                'product_id': None,
                'matches': matches,
                'probability': 0.0
            }
    except Exception as e:
        logger.error(f"Exception during product prediction: {str(e)}")
        logger.debug(traceback.format_exc())
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.get('/mlflow/versions')
def list_versions():
    """
    Lista de versiones del modelo entrenado de predicciones.
    """
    logger.info("Listing MLflow model versions")
    try:
        logger.debug("Retrieving SIFT_Product_Registry experiment")
        experiment = mlflow.get_experiment_by_name("SIFT_Product_Registry")
        if not experiment:
            logger.warning("SIFT_Product_Registry experiment not found")
            return []
        
        logger.debug(f"Experiment found, retrieving runs for experiment_id: {experiment.experiment_id}")
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            run_view_type=ViewType.ACTIVE_ONLY,
            order_by=["attribute.start_time DESC"]
        )
        
        logger.info(f"Retrieved {len(runs)} model versions")
        versions = []
        for _, run in runs.iterrows():
            version_info = {
                'run_id': run['run_id'],
                'date': run['start_time'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(run['start_time'], 'strftime') else str(run['start_time']),
                'product_count': int(run['metrics.product_count']) if 'metrics.product_count' in run and not np.isnan(run['metrics.product_count']) else 0
            }
            versions.append(version_info)
            logger.debug(f"Version added: {version_info['run_id']}, products: {version_info['product_count']}")
        
        return versions
    except Exception as e:
        logger.error(f"Exception while listing MLflow versions: {str(e)}")
        logger.debug(traceback.format_exc())
        return JSONResponse(status_code=500, content={'error': str(e)})



class RestoreRequest(BaseModel):
    run_id: str

@router.post('/mlflow/restore')
def restore_version(request: RestoreRequest):
    """
    Lista para restaurar versiones de modelos entrenados.
    """
    logger.info(f"Model version restoration requested - run_id: {request.run_id}")
    run_id = request.run_id
    if not run_id:
        logger.warning("No run_id provided for restoration")
        return JSONResponse(status_code=400, content={'error': 'No run_id provided'})
    
    try:
        logger.debug(f"Downloading artifacts for run_id: {run_id}")
        artifact_uri = f"runs:/{run_id}/sift_data.pkl"
        downloaded_path = mlflow.artifacts.download_artifacts(artifact_uri=artifact_uri)
        logger.debug(f"Artifacts downloaded to: {downloaded_path}")
        
        logger.debug(f"Copying downloaded model to {SIFT_STORAGE}")
        shutil.copy(downloaded_path, SIFT_STORAGE)
        
        logger.debug("Reloading SIFT engine database")
        sift_engine.load_database()
        
        db_size = len(sift_engine.database)
        logger.info(f"Model version restored successfully - run_id: {run_id}, database size: {db_size}")
        return {'message': f'Restored version {run_id}', 'count': db_size}
    except Exception as e:
        logger.error(f"Exception during model restoration: {str(e)}")
        logger.debug(traceback.format_exc())
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post('/analyze_video')
async def analyze_video(video: UploadFile = File(...)):
    """
    Sube un video, lo procesa para detectar productos y transcribir audio,
    y retorna el guion anotado.
    """
    logger.info(f"Video analysis requested - filename: {video.filename}")
    temp_file_path = f"temp_{video.filename}"
    try:
        logger.debug(f"Writing uploaded video to temporary file: {temp_file_path}")
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        
        logger.debug("Processing video")
        result_text = process_video(temp_file_path, sift_engine)
        logger.info(f"Video analysis completed successfully - filename: {video.filename}")
        
        return {"script": result_text}
    except Exception as e:
        logger.error(f"Exception during video analysis: {str(e)}")
        logger.debug(traceback.format_exc())
        return JSONResponse(status_code=500, content={'error': str(e)})
    finally:
        if os.path.exists(temp_file_path):
            logger.debug(f"Cleaning up temporary file: {temp_file_path}")
            os.remove(temp_file_path)


class ChatRequest(BaseModel):
    message: str
    image: Optional[str] = None

@router.post('/chat')
async def chat(request: ChatRequest):
    """
    Endpoint para recibir mensajes de texto y opcionalmente imágenes.
    Detecta automáticamente nombres de productos en el texto y los anota con SKU-IDs.
    Retorna respuestas en formato de mensajes.
    """
    logger.info(f"Chat message received - length: {len(request.message)} characters")
    try:
        message = request.message
        image = request.image
        
        logger.debug("Annotating message with product SKU-IDs")
        annotated_message = annotate_text_with_csv(message, csv_path="products.csv")
        
        products_detected = "(SKU:" in annotated_message
        
        if products_detected:
            logger.info("Products detected in message")
            response_text = f"He detectado productos en tu mensaje:\n\n{annotated_message}"
        else:
            logger.debug("No products detected in message")
            response_text = f"Mensaje recibido: {message}\n\nNo se detectaron productos registrados en el mensaje."
        
        if image:
            logger.debug("Image provided with message")
            response_text += "\n\n(Imagen recibida - procesamiento pendiente)"
        
        logger.info("Chat response prepared successfully")
        return {
            "content": response_text,   
        }
    except Exception as e:
        logger.error(f"Exception during chat processing: {str(e)}")
        logger.debug(traceback.format_exc())
        return JSONResponse(status_code=500, content={'error': str(e)})


