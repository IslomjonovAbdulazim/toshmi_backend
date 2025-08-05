from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 10080
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    MAX_IMAGE_SIZE: int = 3 * 1024 * 1024
    
    # Additional fields from .env
    BOT_TOKEN: str = ""
    ADMIN_CHAT_ID: str = ""
    HOST: str = "0.0.0.0"
    PORT: str = "8000"
    DEBUG: str = "True"
    APP_NAME: str = "Dunya Jewellery Bot"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields that aren't defined


settings = Settings()