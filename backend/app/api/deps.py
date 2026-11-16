from typing import Optional
from fastapi import Header, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User


def get_current_user_id(
    x_user_id: Optional[str] = Header(None, description="Optional custom user ID for testing multi-user tenancy")
) -> int:
    """
    Returns the active user ID. Defaults to DEFAULT_USER_ID (1) for single demo user mode.
    """
    if x_user_id and x_user_id.isdigit():
        return int(x_user_id)
    return settings.DEFAULT_USER_ID
