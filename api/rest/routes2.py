import base64
import os
import shutil
import uuid
from typing import List, Optional

import cv2
import mlflow
import numpy as np
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
import traceback
from fastapi.responses import JSONResponse
from mlflow.entities import ViewType


# este es el motor de reconocimiento de productos
from ml.models.sift_engine import get_sift_engine
from services.bgRemover import process_image_bytes
from services.video_service import process_video

router = APIRouter()

SIFT_STORAGE = "sift_data.pkl"

sift_engine = get_sift_engine(str(SIFT_STORAGE))

def find_optimal_threshold(cv_image, cv_mask, target_points=1500, tolerance=50):
    """
    Encuentra el threshold optimo para obtener ~target_points keypoints.
    Retorna (best_threshold, best_vis_image, best_count).
    """
    low = 0.001
    high = 0.2
    best_vis = None
    best_count = -1
    best_th = 0.04
    
    for _ in range(8):
        mid = (low + high) / 2
        vis_img, count = sift_engine.detect_keypoints_vis(cv_image, mask=cv_mask, contrast_threshold=mid)
        
        if best_vis is None or abs(count - target_points) < abs(best_count - target_points):
            best_vis = vis_img
            best_count = count
            best_th = mid
        
        if abs(count - target_points) <= tolerance:
            break
            
        if count < target_points:
            high = mid
        else:
            low = mid
            
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
    try:
        # 1. Leer imagen original
        input_bytes = await image.read()
        
        # 2. Remover fondo
        processed_bytes = process_image_bytes(input_bytes)
        
        # Guardar imagen procesada para verificacion
        # try:
        #      os.makedirs("products_images", exist_ok=True)
        #      safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        #      image_path = os.path.join("products_images", f"{safe_name}.png")
        #      with open(image_path, "wb") as f:
        #          f.write(processed_bytes)
        #      print(f"Saved processed image to {image_path}")
        # except Exception as e:
        #      print(f"Failed to save image: {e}")
        #      traceback.print_exc()

        # 3. Convertir a numpy/opencv
        nparr = np.frombuffer(processed_bytes, np.uint8)
        cv_image_rgba = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED) # Keep alpha
        
        if cv_image_rgba is None:
             return JSONResponse(status_code=400, content={'error': 'Could not process image'})
             
        # Separar canales: RGB para imagen, Alpha para máscara
        if cv_image_rgba.shape[2] == 4:
            cv_image = cv2.cvtColor(cv_image_rgba, cv2.COLOR_BGRA2BGR)
            cv_mask = cv_image_rgba[:, :, 3] # Canal Alpha
        else:
            # Si por alguna razón no tiene alpha (rembg falló o devolvió RGB), usamos todo
            cv_image = cv_image_rgba
            cv_mask = None

        # Threshold mask to be binary just in case
        if cv_mask is not None:
             _, cv_mask = cv2.threshold(cv_mask, 127, 255, cv2.THRESH_BINARY)
        
        # 4. Calcular mejor threshold
        optimal_threshold, _, _ = find_optimal_threshold(cv_image, cv_mask)
        print(f"Registering with optimal threshold: {optimal_threshold}")

        # 5. Generar ID único para el producto
        product_id = str(uuid.uuid4())

        # Registrar con los parámetros calculados
        success, msg = sift_engine.register_product(name, product_id, cv_image, mask=cv_mask, contrast_threshold=optimal_threshold)
        
        if success:
            return JSONResponse(status_code=200, content={'message': msg, 'threshold': optimal_threshold, 'product_id': product_id})
        else:
            return JSONResponse(status_code=500, content={'error': msg})

    except Exception as e:
        print("Error during registration:")
        traceback.print_exc()
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
    try:
        # 1. Leer imagen original
        input_bytes = await image.read()
        
        # 2. Remover fondo
        processed_bytes = process_image_bytes(input_bytes)
        
        # 3. Convertir a numpy/opencv
        nparr = np.frombuffer(processed_bytes, np.uint8)
        cv_image_rgba = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
        if cv_image_rgba is None:
            return JSONResponse(status_code=400, content={'error': 'Could not process image'})
            
        if cv_image_rgba.shape[2] == 4:
            cv_image = cv2.cvtColor(cv_image_rgba, cv2.COLOR_BGRA2BGR)
            cv_mask = cv_image_rgba[:, :, 3]
        else:
            cv_image = cv_image_rgba
            cv_mask = None

        if cv_mask is not None:
             _, cv_mask = cv2.threshold(cv_mask, 127, 255, cv2.THRESH_BINARY)
             
        # 4. Encontrar mejor threshold para target 1500 puntos
        best_th, best_vis, best_count = find_optimal_threshold(cv_image, cv_mask)
        
        # Encode return
        _, buffer = cv2.imencode('.jpg', best_vis)
        vis_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            'keypoint_image': vis_base64,
            'count': best_count,
            'optimized_threshold': round(best_th, 5)
        }
    except Exception as e:
        print("Error during preview keypoints:")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post('/predict')
async def predict(image: UploadFile = File(...)):
    """
    Identificación de producto en la imagen subida.
    """
    try:
        img_bytes = await image.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if cv_image is None:
             return JSONResponse(status_code=400, content={'error': 'Invalid image'})

        product_match, matches = sift_engine.identify_product(cv_image)  # identifica el producto
        
        if product_match:
            return {
                'label': product_match['name'],
                'product_id': product_match['id'],
                'matches': matches,
                'probability': 1.0 # SIFT is deterministic "match found", simulated prob
            }
        else:
            return {
                'label': 'Unknown',
                'product_id': None,
                'matches': matches,
                'probability': 0.0
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.get('/mlflow/versions')
def list_versions():
    """
    Lista de versiones del modelo entrenado de predicciones.
    """
    try:
        experiment = mlflow.get_experiment_by_name("SIFT_Product_Registry")
        if not experiment:
            return []
        
        # ordenados desde el mas reciente
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            run_view_type=ViewType.ACTIVE_ONLY,
            order_by=["attribute.start_time DESC"]
        )
        
        versions = []
        for _, run in runs.iterrows():
            versions.append({
                'run_id': run['run_id'],
                'date': run['start_time'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(run['start_time'], 'strftime') else str(run['start_time']),
                'product_count': int(run['metrics.product_count']) if 'metrics.product_count' in run and not np.isnan(run['metrics.product_count']) else 0
            })
        return versions
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


from pydantic import BaseModel

class RestoreRequest(BaseModel):
    run_id: str

@router.post('/mlflow/restore')
def restore_version(request: RestoreRequest):
    """
    Lista para restaurar versiones de modelos entrenados.
    """
    run_id = request.run_id
    if not run_id:
         return JSONResponse(status_code=400, content={'error': 'No run_id provided'})
    
    try:
        # Download (downloads to a temp directory)
        artifact_uri = f"runs:/{run_id}/sift_data.pkl"
        downloaded_path = mlflow.artifacts.download_artifacts(artifact_uri=artifact_uri)
        
        # Overwrite current database
        shutil.copy(downloaded_path, SIFT_STORAGE)
        
        # Reload memory
        sift_engine.load_database()
        
        return {'message': f'Restored version {run_id}', 'count': len(sift_engine.database)}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post('/analyze_video')
async def analyze_video(video: UploadFile = File(...)):
    """
    Sube un video, lo procesa para detectar productos y transcribir audio,
    y retorna el guion anotado.
    """
    temp_file_path = f"temp_{video.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
            
        # Process video
        # Note: process_video encapsulates the logic from videoIdent.py
        result_text = process_video(temp_file_path, sift_engine)
        
        return {"script": result_text}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


class ChatRequest(BaseModel):
    message: str
    image: Optional[str] = None  # Base64 encoded image or URL


@router.post('/chat')
async def chat(request: ChatRequest):
    """
    Endpoint para recibir mensajes de texto y opcionalmente imágenes.
    Retorna respuestas en formato de mensajes.
    """
    try:
        message = request.message
        image = request.image
        
        # Aquí puedes procesar el mensaje y la imagen según tu lógica
        # Por ahora, retornamos una respuesta simple
        
        response_text = f"Recibí tu mensaje: {message}"
        
        # Formato de respuesta esperado por el frontend
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": response_text,
                    "file": None,  # Aquí puedes agregar archivos si es necesario
                    "messages": "Hola mundo"
                }
            ]
        }
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})

