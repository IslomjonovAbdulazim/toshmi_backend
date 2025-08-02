from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 10080
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    MAX_IMAGE_SIZE: int = 3 * 1024 * 1024

    class Config:
        env_file = ".env"


settings = Settings()