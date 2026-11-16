from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.audit_log import AuditLog


class AuditService:
    """
    Immutable Audit Logging Subsystem
    ---------------------------------
    Provides append-only tracking of all security, data, and permission actions.
    This log is deliberately read-only to external clients: records can never
    be edited or removed through the API.
    """

    @staticmethod
    def record_action(
        db: Session,
        user_id: int,
        action: str,
        result: str,
        event_type: Optional[str] = None
    ) -> AuditLog:
        """
        Atomically appends a new audit record to the database.
        
        Parameters:
        - action: The operation attempted (e.g., 'CREATE_EVENT', 'GET_EVENT_DETAIL', 'PERMISSION_SET_OFF')
        - result: Outcome status (e.g., 'ALLOWED', 'DENIED', 'CREATED', 'DELETED', 'UPDATED')
        - event_type: Targeted category, if applicable (e.g., 'location', 'conversation')
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            event_type=event_type,
            result=result,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def get_logs(
        db: Session,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[AuditLog], int]:
        """
        Retrieves paginated audit log entries for a user, ordered from newest to oldest.
        Strictly scoped by user_id for multi-tenant data isolation.
        """
        query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
        total = query.count()
        items = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
        return items, total
