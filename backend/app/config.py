import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANONICAL_DB_PATH = os.path.join(BACKEND_DIR, "smartattend.db")

class Settings(BaseSettings):
    APP_NAME: str = "AIoT SmartAttend Backend"
    DATABASE_URL: str = f"sqlite:///{CANONICAL_DB_PATH}"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "student_images")
    MAX_UPLOAD_SIZE_MB: int = 10
    MIN_FACE_CONFIDENCE: float = 0.85

    # Face Detector Selection
    DETECTOR_BACKEND: str = "SCRFD" # Default primary detector: "SCRFD" (InsightFace SCRFD-10G), with "YOLO" fallback

    # InsightFace SCRFD-10G Model Parameters
    SCRFD_MODEL_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "weights", "scrfd_10g_bnkps.onnx")
    SCRFD_CONFIDENCE_THRESHOLD: float = 0.40
    SCRFD_NMS_THRESHOLD: float = 0.40
    SCRFD_INPUT_SIZE: int = 640
    SCRFD_MIN_FACE_SIZE: int = 10
    SCRFD_ENABLE_TILED_INFERENCE: bool = True # Automatically enables tiled windowing for large classroom images (> 1200px)
    SCRFD_TILE_SIZE: int = 640
    SCRFD_TILE_OVERLAP: float = 0.25
    SCRFD_DEVICE: str = "cpu" # Default CPU, CUDA automatically detected and utilized if available

    # YOLOv11n-face Model Parameters (Preserved for benchmarking & fallback)
    YOLO_MODEL_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "weights", "yolov11n-face.pt")
    YOLO_CONFIDENCE_THRESHOLD: float = 0.40
    YOLO_IOU_THRESHOLD: float = 0.45
    YOLO_INFERENCE_SIZE: int = 640
    YOLO_DEVICE: str = "cpu" # Default to cpu, automatically detects cuda if available and requested

    # Stage 2 Real Face Recognition Parameters
    MODEL_NAME: str = "ArcFace-MobileFaceNet-v2"
    EMBEDDING_DIMENSION: int = 512
    FACE_RECOGNITION_THRESHOLD: float = 0.70
    FACE_AMBIGUITY_THRESHOLD: float = 0.08 # If diff between top-1 and top-2 candidate similarity < 0.08, flag as ambiguous
    AUTO_MARK_ABSENT_ON_PHOTO: bool = False # Configured attendance workflow: do not mark undetected students absent from single photo

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = "" # Anon / Publishable key
    SUPABASE_SERVICE_ROLE_KEY: str = "" # Trusted backend-only service key
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_STORAGE_BUCKET_CLASSROOM: str = "classroom-images"
    SUPABASE_STORAGE_BUCKET_STUDENTS: str = "student-enrollments"

    # Institutional & Operational Parameters
    INSTITUTION_TIMEZONE: str = "Asia/Kolkata"
    MAX_IMAGE_DIMENSION: int = 4096 # Max width/height to prevent DoS via decompression bombs

    # Security & Auth Settings
    SECRET_KEY: str = "smartattend-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DEVICE_API_KEY: str = "smartattend-esp32-secret-key-2026"

    model_config = SettingsConfigDict(
        env_file=[
            ".env",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        ],
        extra="ignore"
    )

settings = Settings()

# Ensure storage directory exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
