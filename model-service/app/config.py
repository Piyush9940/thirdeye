"""Configuration settings for the Earth Systems Trend Detective ML Inference Service."""

import os
from pathlib import Path

class Settings:
    SERVICE_NAME: str = "Earth Systems Trend Detective - ML Inference Service"
    SERVICE_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Model storage path: check local model-service package first, then root models
    APP_DIR: Path = Path(__file__).resolve().parent
    SERVICE_ROOT: Path = APP_DIR.parent
    DEFAULT_PACKAGE_DIR: Path = SERVICE_ROOT / "models" / "production_reference"
    
    MODEL_PACKAGE_DIR: Path = Path(os.getenv("MODEL_PACKAGE_DIR", str(DEFAULT_PACKAGE_DIR)))
    
    # Target device for PyTorch inference (CPU by default)
    INFERENCE_DEVICE: str = os.getenv("INFERENCE_DEVICE", "cpu")
    
    # Optional service-to-service API key for protection
    MODEL_SERVICE_API_KEY: str = os.getenv("MODEL_SERVICE_API_KEY", "")
    
    # CORS configuration
    CORS_ORIGINS: list[str] = ["*"]

settings = Settings()

# Fallback path if bundled directory isn't present
if not settings.MODEL_PACKAGE_DIR.exists():
    fallback_path = settings.SERVICE_ROOT.parent / "models" / "production_reference"
    if fallback_path.exists():
        settings.MODEL_PACKAGE_DIR = fallback_path
