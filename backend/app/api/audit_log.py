from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse
from app.schemas.error import ValidationErrorResponse
from app.services.audit_service import AuditService

router = APIRouter(tags=["Audit Log"])


@router.get(
    "/audit-log",
    response_model=AuditLogListResponse,
    summary="Get read-only audit log entries",
    responses={
        200: {"description": "Immutable audit entries returned in descending timestamp order."},
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error: invalid pagination limit or offset."
        }
    }
)
@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    include_in_schema=False
)
def get_audit_log(
    limit: int = Query(100, ge=1, le=500, description="Max audit entries to retrieve (1-500)"),
    offset: int = Query(0, ge=0, description="Offset for pagination (>= 0)"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Returns an immutable, chronologically ordered audit trail of privacy and data actions.
    This endpoint is strictly read-only.
    """
    items, total = AuditService.get_logs(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(item) for item in items],
        total=total
    )
