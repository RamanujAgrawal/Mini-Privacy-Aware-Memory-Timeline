from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_serializer


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    user_id: int
    action: str
    event_type: Optional[str]
    result: str

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime, _info) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
