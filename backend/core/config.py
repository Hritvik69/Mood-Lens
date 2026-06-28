import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App General Settings
    APP_NAME: str = "EmotionVision AI"
    DEBUG: bool = False
    
    # Server configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    BACKEND_DIR: Path = Path(__file__).resolve().parent.parent
    MODEL_DIR: Path = BASE_DIR / "models"
    DATABASE_PATH: Path = BACKEND_DIR / "emotionvision_ai.db"
    
    # Model Configurations
    MODEL_NAME: str = "emotion-ferplus-8.onnx"
    # Stable Hugging Face ONNX Model Zoo download link
    MODEL_URL: str = "https://huggingface.co/onnxmodelzoo/emotion-ferplus-8/resolve/main/emotion-ferplus-8.onnx"
    MODEL_SHA256: str = "88bb2b8eaebc5db4d1a084c0c8eb4f9cd9e71234b3f86e39265f02bc70b69680" # Standard hash for emotion-ferplus-8.onnx
    
    # Confidence and thresholds
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.5
    DEFAULT_PREDICTION_INTERVAL: float = 0.033  # ~30 FPS processing interval
    
    # Hardware acceleration preferences
    PREFERRED_PROVIDERS: List[str] = [
        "CUDAExecutionProvider",
        "DirectMLExecutionProvider",
        "OpenVINOExecutionProvider",
        "CPUExecutionProvider"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Ensure model directory exists
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
