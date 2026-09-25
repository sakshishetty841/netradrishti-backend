import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NetraDrishti API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "netradrishti_super_secret_jwt_key_rural_health_2026_sih")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./netradrishti.db"
    )
    
    # Storage
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")
    MEDIA_DIR: str = os.getenv("MEDIA_DIR", "./media")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "*"
    ]
    
    # AI Model Metadata
    MODEL_NAME: str = "NetraDrishti-DR-Inference"
    MODEL_VERSION: str = "prototype-v1"
    EXPLAINABILITY_VERSION: str = "gradcam-v1"
    
    # Security / OTP
    OTP_EXPIRE_MINUTES: int = 10
    MAX_OTP_ATTEMPTS: int = 5
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
