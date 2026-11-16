from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def record_action(
        db: Session,
        user_id: int,
        action: str,
        result: str,
        event_type: Optional[str] = None
    ) -> AuditLog:
        """
        Atomically records a privacy or data action in the audit log.
        Result is typically 'ALLOWED', 'DENIED', 'CREATED', 'DELETED', 'UPDATED'.
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
        Retrieves paginated audit log entries for a user, sorted descending by timestamp.
        Audit log is strictly read-only.
        """
        query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
        total = query.count()
        items = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
        return items, total
