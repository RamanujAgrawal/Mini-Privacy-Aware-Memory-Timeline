from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.permission import PermissionUpdate, PermissionResponse, PermissionsState
from app.schemas.error import ErrorResponse, ValidationErrorResponse
from app.services.privacy_service import PrivacyService

router = APIRouter(tags=["Privacy Permissions"])


@router.get(
    "/permissions",
    response_model=PermissionsState,
    summary="Get user privacy permission settings",
    responses={
        200: {"description": "Active permissions map returned for all 4 core categories."}
    }
)
def get_permissions(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Returns the ON/OFF state for all 4 categories:
    - conversation
    - location
    - physiological
    - note
    """
    perms = PrivacyService.get_permissions(db, user_id)
    return PermissionsState(permissions=perms)


@router.put(
    "/permissions",
    response_model=PermissionResponse,
    summary="Update a category permission (ON/OFF)",
    responses={
        200: {"description": "Permission updated and recorded in audit trail."},
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error: invalid category or boolean value."
        }
    }
)
def update_permission(
    payload: PermissionUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Toggles a category's visibility ON or OFF.
    Changes immediately affect subsequent event retrieval requests and are recorded in the audit log.
    """
    updated = PrivacyService.update_permission(
        db=db,
        user_id=user_id,
        category=payload.category.value if hasattr(payload.category, "value") else str(payload.category),
        is_enabled=payload.is_enabled
    )
    return PermissionResponse.model_validate(updated)
