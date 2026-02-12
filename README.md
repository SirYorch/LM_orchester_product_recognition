# Backend de Reconocimiento de Productos y Análisis de Video

Este es un proyecto base en FastAPI que combina visión por computadora y transcripción de audio para gestionar y reconocer productos en videos.

## Estructura

```
business_backend/
├── main.py                 # Punto de entrada de la aplicación FastAPI
├── services/
│   ├── video_service.py    # Lógica central: SIFT + Whisper
│   └── bgRemover.py        # Eliminación de fondo automática
│
├── api/rest/
│   └── routes2.py          # Endpoints principales (REST)
│
├── ml/
│   ├── models/             
│   │   └── sift_engine.py  # Motor de reconocimiento SIFT
│
├── sift_data.pkl           # Base de datos persistente de features (productos)
├── products.csv            # Metadatos de productos (ID, Nombre)
└── trans_whisper.py        # Módulo de prueba para transcripción
```

## Variables de Entorno

El proyecto funciona principalmente de manera local, pero asegúrate de tener las siguientes dependencias del sistema:

- **FFmpeg**: Requerido por `whisper` para procesar audio.
  ```bash
  sudo apt update && sudo apt install ffmpeg
  ```
- **OpenCV**: Requerido para el procesamiento de imágenes.

## Ejecución

Para iniciar el servidor de desarrollo:

```bash
uvicorn main:app --reload --port 8000
```

- API Docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/health

## Endpoints (API REST)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/register` | Registra un nuevo producto. Sube imagen + nombre. Elimina fondo automáticamente. |
| `POST` | `/analyze_video` | Sube un video para obtener una transcripción enriquecida con detección de productos. |
| `POST` | `/chat` | Envía texto/imagen. Detecta productos mencionados y anota sus SKUs. |
| `POST` | `/preview_keypoints` | Previsualiza cuántos puntos clave SIFT se detectan en una imagen. |
| `GET` | `/mlflow/versions` | Lista las versiones guardadas de la base de datos de productos. |
| `POST` | `/mlflow/restore` | Restaura una versión anterior de la base de datos de productos. |

### Ejemplos de Uso

#### 1. Registrar un Producto
Sube una imagen del producto (e.g., una botella de refresco). El sistema:
1. Elimina el fondo.
2. Calcula automáticamente el contraste óptimo para extraer ~1500 puntos clave (SIFT).
3. Guarda los descriptores en `sift_data.pkl`.
4. Retorna el ID generado (`UUID`).

#### 2. Analizar Video
Sube un video MP4 donde aparezcan productos y se hable de ellos.
- **Visión**: Detecta productos frame a frame mediante coincidencia de puntos clave (SIFT).
- **Audio**: Transcribe el audio a texto usando el modelo `base` de Whisper.
- **Resultado**: Un guion de texto donde las menciones a productos están anotadas con sus SKUs si fueron vistos o mencionados.

## Funcionamiento de los Módulos

### Módulo de Visión (SIFT Engine)
Utiliza el algoritmo **SIFT (Scale-Invariant Feature Transform)** para ser robusto a cambios de escala y rotación.
- Al registrar, se extraen descriptores de la imagen "ideal".
- Al analizar video, se comparan los descriptores de cada frame con la base de datos usando `BFMatcher` (Brute Force Matcher) con ratio test de Lowe.

### Módulo de Audio (Whisper)
Utiliza el modelo **Whisper de OpenAI** (versión `base` local) para convertir voz a texto.
- Soporta múltiples idiomas, pero está configurado principalmente para español (`language="es"`).
- Segmenta el audio y alinea las transcripciones con los timestamps del video.

### Módulo de Anotación (`/chat`, Video)
Cruza la información de texto y visión.
- Si el texto menciona "Coca-Cola" y el sistema visual detectó una Coca-Cola en ese segundo, la transcripción final dirá: "Coca-Cola (SKU: 1234-...)".
- Utiliza `products.csv` como fuente de verdad para nombres de productos y sus IDs.

## MLflow (Versionado)
El sistema rastrea cada vez que se actualiza la base de datos de productos (`sift_data.pkl`).
- Permite listar versiones históricas.
- Permite "viajar en el tiempo" y restaurar un estado anterior de la base de conocimiento de productos si algo sale mal.
