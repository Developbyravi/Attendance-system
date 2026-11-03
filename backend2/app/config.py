import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application Settings for SmartAttend AIoT Backend2.
    Loads configurations from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server Core
    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8002
    DEBUG: bool = True
    APP_TITLE: str = "SmartAttend AIoT Backend2"
    APP_VERSION: str = "2.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./smartattend.db"
    DB_ECHO: bool = False

    # Optional Supabase Integration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Security & JWT
    JWT_SECRET: str = "smartattend-dev-insecure-secret-key-change-in-production-32bytes"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours

    # Face AI Models
    SCRFD_MODEL_PATH: str = "weights/scrfd_10g_bnkps.onnx"
    FACE_DETECTOR_MODEL: str = "InsightFace SCRFD-10G"
    FACE_RECOGNITION_MODEL: str = "ArcFace-MobileFaceNet"
    FACE_DETECTION_THRESHOLD: float = 0.50
    FACE_MATCH_THRESHOLD: float = 0.70
    FACE_AMBIGUITY_THRESHOLD: float = 0.08
    EMBEDDING_DIMENSION: int = 512
    INFERENCE_DEVICE: str = "cpu"

    # High-Resolution Classroom Inference Settings
    ENABLE_TILED_INFERENCE: bool = True
    TILE_SIZE: int = 640
    TILE_OVERLAP: float = 0.25

    # Storage & Uploads
    STORAGE_DRIVER: str = "local" # "local" or "supabase"
    STORAGE_BUCKET: str = "smartattend-storage"
    UPLOAD_DIR: str = "./uploads"

    # CORS Allowed Origins
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8002"

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def base_dir(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @property
    def resolved_scrfd_path(self) -> str:
        if os.path.isabs(self.SCRFD_MODEL_PATH):
            return self.SCRFD_MODEL_PATH
        return os.path.join(self.base_dir, self.SCRFD_MODEL_PATH)

    @property
    def resolved_upload_dir(self) -> str:
        if os.path.isabs(self.UPLOAD_DIR):
            return self.UPLOAD_DIR
        return os.path.join(self.base_dir, self.UPLOAD_DIR)

settings = Settings()

