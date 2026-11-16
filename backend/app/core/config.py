import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Resolve root directory of project (where .env, run.py, and chronis.db live)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.dirname(APP_DIR)
ROOT_DIR = os.path.dirname(BACKEND_DIR)
ENV_FILE = os.path.join(ROOT_DIR, ".env")
DEFAULT_DB_PATH = os.path.join(ROOT_DIR, "chronis.db").replace("\\", "/")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Chronis Privacy Timeline"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"
    TEST_DATABASE_URL: str = "sqlite:///:memory:"
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    DEFAULT_USER_ID: int = 1
    
    model_config = SettingsConfigDict(
        env_file=ENV_FILE if os.path.exists(ENV_FILE) else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
