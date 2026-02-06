import cv2
import whisper
from collections import defaultdict
from ml.models.sift_engine import get_sift_engine

# ==================================================
# CONFIGURACIÓN
# ==================================================
VIDEO_PATH = "video_test.mp4"
SIFT_DB_PATH = "sift_data.pkl"

FRAME_EVERY_SECONDS = 1
MIN_MATCHES = 120

WINDOW_SIZE = 1.0          # segundos
MIN_FRAMES_PER_SKU = 5     # votos mínimos en la ventana
MIN_WORDS_TEXT = 4         # evita "gracias", "ok", etc.


# ==================================================
# 1. CARGAR MODELOS
# ==================================================
print("Cargando modelos...")
sift = get_sift_engine(SIFT_DB_PATH)
whisper_model = whisper.load_model("base")


# ==================================================
# 2. DETECCIÓN VISUAL (SIFT MULTIETIQUETA)
# ==================================================
print("Analizando video con SIFT...")

cap = cv2.VideoCapture(VIDEO_PATH)
fps = cap.get(cv2.CAP_PROP_FPS)

detections = []  # detecciones crudas por frame
frame_idx = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    time_sec = frame_idx / fps

    if int(time_sec) % FRAME_EVERY_SECONDS == 0:
        visible = []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp_q, des_q = sift.sift.detectAndCompute(gray, None)

        if des_q is not None:
            for sku, des_ref in sift.database.items():
                bf = cv2.BFMatcher()
                matches = bf.knnMatch(des_ref, des_q, k=2)

                good = []
                for pair in matches:
                    if len(pair) < 2:
                        continue
                    m, n = pair
                    if m.distance < 0.75 * n.distance:
                        good.append(m)

                if len(good) >= MIN_MATCHES:
                    visible.append(sku)

        if visible:
            detections.append({
                "time": round(time_sec, 2),
                "skus": visible
            })

    frame_idx += 1

cap.release()


# ==================================================
# 3. AGRUPAR POR VENTANAS + VOTACIÓN
# ==================================================
def aggregate_detections(detections, window_size=1.0, min_frames=5):
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


detections = aggregate_detections(
    detections,
    window_size=WINDOW_SIZE,
    min_frames=MIN_FRAMES_PER_SKU
)

print("Detecciones visuales agregadas:", detections)


# ==================================================
# 4. TRANSCRIPCIÓN DE AUDIO (WHISPER)
# ==================================================
print("Transcribiendo audio con Whisper...")

result = whisper_model.transcribe(VIDEO_PATH, language="es")

segments = [
    {
        "start": seg["start"],
        "end": seg["end"],
        "text": seg["text"].strip()
    }
    for seg in result["segments"]
]


# ==================================================
# 5. INSERTAR SKUs EN TEXTO NATURAL
# ==================================================
def annotate_text(segments, detections, min_presence_ratio=0.6):
    final_parts = []

    for seg in segments:
        text = seg["text"]

        if len(text.split()) < MIN_WORDS_TEXT:
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



# ==================================================
# 6. SALIDA FINAL DEL AGENTE
# ==================================================
final_text = annotate_text(segments, detections)

print("\n================ SALIDA DEL AGENTE ================\n")
print(final_text)
print("\n==================================================\n")
