from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:password@localhost/education_center"

    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # File Upload
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_profile_image_size: int = 3 * 1024 * 1024  # 3MB

    # Environment
    environment: str = "development"
    debug: bool = True

    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False


settings = Settings()