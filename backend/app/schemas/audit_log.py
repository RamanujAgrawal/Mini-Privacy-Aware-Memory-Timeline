from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    user_id: int
    action: str
    event_type: Optional[str]
    result: str

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
