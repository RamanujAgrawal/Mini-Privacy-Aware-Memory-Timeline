from typing import Optional
from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.user import User


def get_current_user_id(
    authorization: Optional[str] = Header(None, description="Optional Bearer JWT token"),
    x_user_id: Optional[str] = Header(None, description="Optional custom user ID for testing multi-user tenancy"),
    db: Session = Depends(get_db)
) -> int:
    """
    Resolves the active authenticated user ID.
    Supports:
      1. JWT Bearer token in 'Authorization: Bearer <token>'
      2. 'X-User-Id' header for test suites
      3. Fallback to DEFAULT_USER_ID (1) for seamless demo mode
    """
    # 1. Check JWT Bearer token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired JWT authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with token not found or deactivated.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id

    # 2. Check X-User-Id header
    if x_user_id and x_user_id.isdigit():
        return int(x_user_id)

    # 3. Default demo user mode
    return settings.DEFAULT_USER_ID
