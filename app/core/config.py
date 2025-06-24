import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE: int = 3 * 1024 * 1024  # 3MB

    class Config:
        env_file = ".env"

settings = Settings()