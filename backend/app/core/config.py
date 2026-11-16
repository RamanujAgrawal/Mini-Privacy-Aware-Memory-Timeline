import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Dynamically resolve absolute project paths so execution works seamlessly
# regardless of which folder terminal commands are invoked from.
# APP_DIR: .../backend/app
# BACKEND_DIR: .../backend
# ROOT_DIR: .../Mini Privacy-Aware Memory Timeline (repository root)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.dirname(APP_DIR)
ROOT_DIR = os.path.dirname(BACKEND_DIR)

ENV_FILE = os.path.join(ROOT_DIR, ".env")
DEFAULT_DB_PATH = os.path.join(ROOT_DIR, "chronis.db").replace("\\", "/")


class Settings(BaseSettings):
    """
    Application Configuration
    -------------------------
    Reads from environment variables and .env file with sensible developer defaults.
    """
    PROJECT_NAME: str = "Chronis Privacy Timeline"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # SQLite file path in the repository root for turnkey evaluation
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"
    TEST_DATABASE_URL: str = "sqlite:///:memory:"
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Seeded demo user ID for turnkey zero-login evaluation
    DEFAULT_USER_ID: int = 1
    
    model_config = SettingsConfigDict(
        env_file=ENV_FILE if os.path.exists(ENV_FILE) else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
