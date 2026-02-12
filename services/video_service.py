import cv2
import whisper
from collections import defaultdict
import os
import csv
import re

# Global variable to cache the whisper model
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("Loading Whisper model (base)...")
        _whisper_model = whisper.load_model("base")
    return _whisper_model

def process_video(video_path, sift_engine, frame_every_seconds=1, min_matches=130):
    """
    Process a video file to detect products and transcribe audio.
    Returns the annotated transcript.
    """
    
    # 1. Visual Detection (SIFT)
    print(f"Analyzing video: {video_path}")
    detections = _detect_products_in_video(video_path, sift_engine, frame_every_seconds, min_matches)
    
    # 2. Aggregation
    aggregated_detections = _aggregate_detections(detections)
    print("Visual detections aggregated:", aggregated_detections)

    # 3. Audio Transcription (Whisper)
    print("Transcribing audio...")
    model = get_whisper_model()
    result = model.transcribe(video_path, language="es")
    print("Transcription completed. Segments:", len(result["segments"]))
    
    segments = [
        {
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip()
        }
        for seg in result["segments"]
    ]

    # 4. Annotation
    final_text = _annotate_text(segments, aggregated_detections)
    
    return final_text

def _detect_products_in_video(video_path, sift_engine, frame_every_seconds, min_matches):
    detections = []
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_idx = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        time_sec = frame_idx / fps

        # Process every N seconds
        if int(time_sec) % frame_every_seconds == 0:
            # Optimize: Skip frames if we just processed this second? 
            # The original logic was: if int(time_sec) % 1 == 0. 
            # This is true for multiple frames within the same second if we don't track integer change.
            # But let's stick to original logic: it checks if the integer part is divisible.
            # If FPS > 1, this condition might trigger multiple times per second unless we are careful.
            # Original code: `if int(time_sec) % FRAME_EVERY_SECONDS == 0:`
            # This actually runs for EVERY frame during the 0th second, 1st second, etc. if FRAME_EVERY_SECONDS=1.
            # Wait, 1 % 1 == 0. 1.1 % 1 != 0 (float). But int(1.1)=1. 
            # So `int(time_sec) % 1 == 0` is ALWAYS true for all seconds.
            # This means it runs for EVERY FRAME. That explains why it might be slow.
            # BUT, let's look at `videoIdent.py` again.
            # `if int(time_sec) % FRAME_EVERY_SECONDS == 0:`
            # If `time_sec` is 0.0, 0.03, ... int is 0. 0 % 1 == 0. Runs for first second.
            # If `time_sec` is 1.0, 1.03... int is 1. 1 % 1 == 0. Runs for second second.
            # So it runs for EVERY frame.
            # I suspect the user intended: process ONE frame every second.
            # I will fix this to process only check once per second interval.
            pass
            
            # Let's implement a more robust "every second" check or stick to original if that was intended.
            # To simulate "once per second", we can check if int(time_sec) > int(prev_time_sec).
            
        frame_idx += 1
    
    # Re-implementing with more efficient loop
    cap.release()
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    current_sec = -1
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        time_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        
        if int(time_sec) > current_sec:
            current_sec = int(time_sec)
            if current_sec % frame_every_seconds == 0:
                # Process this frame
                visible = []
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                kp_q, des_q = sift_engine.sift.detectAndCompute(gray, None)

                if des_q is not None:
                    # Accessing internal database of SIFT engine
                    for product_id, product_data in sift_engine.database.items():
                        if product_data is None or product_data.get("descriptors") is None:
                            continue
                        
                        des_ref = product_data["descriptors"]
                        product_name = product_data["name"]
                        bf = cv2.BFMatcher()
                        matches = bf.knnMatch(des_ref, des_q, k=2)

                        good = []
                        for pair in matches:
                            if len(pair) < 2:
                                continue
                            m, n = pair
                            if m.distance < 0.75 * n.distance:
                                good.append(m)

                        if len(good) >= min_matches:
                            visible.append(product_name)

                if visible:
                    detections.append({
                        "time": round(time_sec, 2),
                        "skus": visible
                    })
                    
    cap.release()
    return detections

def _aggregate_detections(detections, window_size=1.0, min_frames=1): 
    # Note: reduced min_frames default because now we might be picking 1 frame per second.
    # Original logic ran on every frame, so 5 frames threshold made sense (assuming 30fps).
    # If we only pick 1 frame per second, min_frames should probably be 1 if we want to detect anything at all in that second.
    # However, to filter noise, maybe we should sample more freq?
    # Let's stick to the user's logic but maybe sample every 5th frame or so if we want "min 5 votes".
    # For now, I'll stick to 1 frame per second and min_frames=1 for robustness in this new approach, 
    # OR I can implement the frame skipping properly to match original density.
    
    # Let's try to match original density: run on every frame.
    # But that is very slow. 
    # Let's look at the original code again.
    # `if int(time_sec) % FRAME_EVERY_SECONDS == 0:`
    # This runs for EVERY frame.
    # I will stick to the safer logic of running on every frame but maybe optimize later.
    pass

# Redefining _detect_products_in_video to match original logic exactly for safety
def _detect_products_in_video(video_path, sift_engine, frame_every_seconds, min_matches):
    detections = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_idx = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        time_sec = frame_idx / fps

        # Original condition: int(time_sec) % FRAME_EVERY_SECONDS == 0
        # If FRAME_EVERY_SECONDS is 1, this is True for every frame.
        if int(time_sec) % frame_every_seconds == 0:
            visible = []
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            kp_q, des_q = sift_engine.sift.detectAndCompute(gray, None)

            if des_q is not None:
                for product_id, product_data in sift_engine.database.items():
                    if product_data is None or product_data.get("descriptors") is None:
                        continue
                    
                    des_ref = product_data["descriptors"]
                    product_name = product_data["name"]

                    
                    
                    
                    bf = cv2.BFMatcher()
                    matches = bf.knnMatch(des_ref, des_q, k=2)
                    good = []
                    for pair in matches:
                        if len(pair) < 2:
                            continue
                        m, n = pair
                        if m.distance < 0.75 * n.distance:
                            good.append(m)

                    if len(good) >= min_matches:
                        visible.append(product_name)
                        # print(f"Producto detectado: {product_name} con {len(good)} buenos matches")

            if visible:
                detections.append({
                    "time": round(time_sec, 2),
                    "skus": visible
                })

        frame_idx += 1
    
    cap.release()
    return detections

def _aggregate_detections(detections, window_size=1.0, min_frames=5):
    windows = defaultdict(list)

    for det in detections:
        window_id = int(det["time"] // window_size)
        windows[window_id].append(det["skus"])

    aggregated = []

    for window_id, sku_lists in windows.items():
        counter = defaultdict(int)

        for skus in sku_lists:
            for sku in skus:
                counter[sku] += 1

        final_skus = [
            sku for sku, count in counter.items()
            if count >= min_frames
        ]

        if final_skus:
            aggregated.append({
                "start": window_id * window_size,
                "end": (window_id + 1) * window_size,
                "skus": final_skus
            })

    return aggregated

def _annotate_text(segments, detections, min_words_text=4, min_presence_ratio=0.6):
    final_parts = []

    for seg in segments:
        text = seg["text"]

        if len(text.split()) < min_words_text:
            final_parts.append(text)
            continue

        sku_counter = defaultdict(int)
        total_windows = 0

        for det in detections:
            overlap = not (
                seg["end"] < det["start"] or
                seg["start"] > det["end"]
            )
            if overlap:
                total_windows += 1
                for sku in det["skus"]:
                    sku_counter[sku] += 1

        final_skus = []
        for sku, count in sku_counter.items():
            if count / max(total_windows, 1) >= min_presence_ratio:
                final_skus.append(sku)

        if final_skus:
            sku_text = ", ".join(f"SKU:{s}" for s in sorted(final_skus))
            text = f"{text} ({sku_text})"

        final_parts.append(text)

    return " ".join(final_parts)


def annotate_text_with_csv(text, csv_path="products.csv", case_sensitive=False):
    """
    Anota un texto detectando nombres de productos del CSV y agregando su SKU-ID.
    
    Args:
        text: Texto a anotar
        csv_path: Ruta al archivo CSV con productos (por defecto: products.csv)
        case_sensitive: Si True, la búsqueda es sensible a mayúsculas/minúsculas
    
    Returns:
        Texto anotado con SKU-IDs
        
    Ejemplo:
        Input: "Me gusta la Coca-Cola y la Pepsi"
        Output: "Me gusta la Coca-Cola (SKU:550e8400-e29b-41d4-a716-446655440000) y la Pepsi (SKU:6ba7b810-9dad-11d1-80b4-00c04fd430c8)"
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
    # Esto evita que nombres cortos reemplacen partes de nombres largos
    products.sort(key=lambda p: len(p['name']), reverse=True)
    
    annotated_text = text
    replacements = []  # Para evitar reemplazos duplicados
    
    for product in products:
        product_name = product['name']
        product_id = product['id']
        
        # Crear patrón de búsqueda
        # \b asegura que coincida con palabras completas
        if case_sensitive:
            pattern = r'\b' + re.escape(product_name) + r'\b'
            flags = 0
        else:
            pattern = r'\b' + re.escape(product_name) + r'\b'
            flags = re.IGNORECASE
        
        # Buscar todas las ocurrencias
        matches = list(re.finditer(pattern, annotated_text, flags=flags))
        
        # Reemplazar de atrás hacia adelante para mantener índices correctos
        for match in reversed(matches):
            start, end = match.span()
            matched_text = annotated_text[start:end]
            
            # Verificar si ya fue anotado (evitar anotar dos veces)
            if "(SKU:" not in annotated_text[end:end+50]:  # Buscar en los próximos 50 caracteres
                replacement = f"{matched_text} (SKU:{product_id})"
                annotated_text = annotated_text[:start] + replacement + annotated_text[end:]
    
    return annotated_text
