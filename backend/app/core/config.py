import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Chronis Privacy Timeline"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "sqlite:///./chronis.db"
    TEST_DATABASE_URL: str = "sqlite:///./test_chronis.db"
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    DEFAULT_USER_ID: int = 1
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
