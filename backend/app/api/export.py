import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user_id
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.event_service import EventService
from app.services.privacy_service import PrivacyService
from app.services.audit_service import AuditService
from app.schemas.export import ExportRequest, ExportResponse, ExportMetadata

router = APIRouter(prefix="/export", tags=["Export & Data Portability"])


def _generate_export_data(
    db: Session,
    user_id: int,
    format_type: str,
    include_audit_trail: bool,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    user = db.query(User).filter(User.id == user_id).first()
    user_name = user.name if user else f"User {user_id}"

    # Retrieve permitted events (privacy filtered and rule redacted)
    events, _ = EventService.get_events(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=5000,
        offset=0
    )

    # Format events list
    event_list = []
    for ev in events:
        ts = ev.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        event_list.append({
            "id": ev.id,
            "timestamp": ts.isoformat(),
            "type": ev.type,
            "title": ev.title,
            "content": ev.content
        })

    # Retrieve audit logs if requested
    audit_list = []
    if include_audit_trail:
        logs, _ = AuditService.get_logs(db=db, user_id=user_id, limit=5000, offset=0)
        for lg in logs:
            lts = lg.timestamp
            if lts.tzinfo is None:
                lts = lts.replace(tzinfo=timezone.utc)
            audit_list.append({
                "id": lg.id,
                "timestamp": lts.isoformat(),
                "action": lg.action,
                "event_type": lg.event_type,
                "result": lg.result
            })

    permissions = PrivacyService.get_permissions(db, user_id)

    # Audit the export action
    AuditService.record_action(
        db=db,
        user_id=user_id,
        action="EXPORT_DATA",
        result=f"EXPORTED_{format_type.upper()}",
        event_type="all"
    )

    metadata = ExportMetadata(
        standard="GDPR Article 20 / CCPA Data Portability Compliant",
        generated_at=datetime.now(timezone.utc).isoformat(),
        user_id=user_id,
        username=user_name,
        event_count=len(event_list),
        audit_log_count=len(audit_list),
        export_format=format_type.lower()
    )

    return metadata, permissions, event_list, audit_list


@router.post("")
def export_data_post(
    req: ExportRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    POST /export: Export permitted memory timeline and audit trail in JSON or CSV format.
    Ensures GDPR/CCPA data portability compliance while respecting active privacy filters.
    """
    metadata, perms, events, audit_trail = _generate_export_data(
        db=db,
        user_id=user_id,
        format_type=req.format,
        include_audit_trail=req.include_audit_trail,
        start_date=req.start_date,
        end_date=req.end_date
    )

    if req.format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["--- TIMELINE EVENTS ---"])
        writer.writerow(["ID", "Timestamp (UTC)", "Category", "Title", "Content"])
        for ev in events:
            writer.writerow([ev["id"], ev["timestamp"], ev["type"], ev["title"], ev["content"]])

        if req.include_audit_trail and audit_trail:
            writer.writerow([])
            writer.writerow(["--- AUDIT TRAIL LOGS ---"])
            writer.writerow(["Log ID", "Timestamp (UTC)", "Action", "Category", "Result"])
            for lg in audit_trail:
                writer.writerow([lg["id"], lg["timestamp"], lg["action"], lg["event_type"], lg["result"]])

        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=chronis_memory_export_{user_id}.csv"
            }
        )

    # Default to JSON
    export_payload = {
        "metadata": metadata.model_dump(),
        "active_permissions": perms,
        "events": events,
        "audit_trail": audit_trail if req.include_audit_trail else []
    }
    return export_payload


@router.get("")
def export_data_get(
    format: str = Query(default="json", description="Export format: 'json' or 'csv'"),
    include_audit_trail: bool = Query(default=True, description="Include audit logs"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    GET /export: Download endpoint for browser and direct HTTP clients.
    """
    req = ExportRequest(format=format, include_audit_trail=include_audit_trail)
    return export_data_post(req=req, db=db, user_id=user_id)
