import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://gen_user:(8Ah)S$aY)lF6t@3d7780415a2721a636acfe11.twc1.net:5432/default_db?sslmode=require"
    JWT_SECRET: str = "UgoxERiU-d3vFK8z-a9lU_mRrN12oWKcUu_zjn1CHZ0"
    JWT_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE: int = 3 * 1024 * 1024  # 3MB

    class Config:
        env_file = ".env"

settings = Settings()