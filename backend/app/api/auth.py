from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserProfile
from app.schemas.error import ErrorResponse, ValidationErrorResponse
from app.services.privacy_service import PrivacyService
from app.services.audit_service import AuditService
from app.api.deps import get_current_user_id

router = APIRouter(prefix="/auth", tags=["Authentication & Multi-Tenancy"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new tenant user with JWT authentication",
    responses={
        201: {"description": "User created and authenticated successfully."},
        400: {"model": ErrorResponse, "description": "Email already registered."},
        422: {"model": ValidationErrorResponse, "description": "Validation failure."}
    }
)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Registers a new tenant user in the database, hashes their password,
    initializes their default privacy controls, and returns a signed JWT access token.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An account with email '{payload.email}' already exists."
        )

    hashed_pw = hash_password(payload.password)
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hashed_pw,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize default privacy permissions for the new user
    PrivacyService.ensure_default_permissions(db, user.id)

    # Record registration in audit log
    AuditService.record_action(
        db=db,
        user_id=user.id,
        action="USER_REGISTER",
        result="CREATED",
        event_type="auth"
    )

    token = create_access_token(user_id=user.id, email=user.email)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        name=user.name,
        email=user.email
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT access token",
    responses={
        200: {"description": "Authentication successful; returns bearer JWT token."},
        401: {"model": ErrorResponse, "description": "Invalid email or password."}
    }
)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates user credentials and issues a signed JWT token.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Record login audit
    AuditService.record_action(
        db=db,
        user_id=user.id,
        action="USER_LOGIN",
        result="ALLOWED",
        event_type="auth"
    )

    token = create_access_token(user_id=user.id, email=user.email)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        name=user.name,
        email=user.email
    )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get authenticated user profile"
)
def get_current_user_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Returns the active authenticated user profile details.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserProfile.model_validate(user)
