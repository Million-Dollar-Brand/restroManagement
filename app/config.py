from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application configuration from environment variables"""

    # Database - must be provided via environment variable in production
    database_url: str
    tenant_schema_prefix: str = "tenant_"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # File Uploads
    upload_dir: str = "/tmp/uploads"
    max_file_size: int = 5242880  # 5MB
    allowed_extensions: str = "jpg,jpeg,png,webp"

    # App
    app_name: str = "TableManager API"
    version: str = "1.0.0"
    description: str = "REST API backend for table management service"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)