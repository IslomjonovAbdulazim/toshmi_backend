import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    MAX_IMAGE_SIZE: int = 3 * 1024 * 1024
    ADMIN_PHONE: str = "+998901234567"
    ADMIN_PASSWORD: str = 'sWk}X2<1#5[*'

    class Config:
        env_file = ".env"

settings = Settings()