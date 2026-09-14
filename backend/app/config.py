import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    YOUTUBE_DATA_API_KEY: str = ""
    COMMONS_API_USER_AGENT: str = "Video2Study/1.0"
    STORAGE_DIR: str = os.path.abspath("./storage")
    PORT: int = 8000
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)