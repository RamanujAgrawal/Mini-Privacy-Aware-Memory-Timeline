from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    format: str = Field(default="json", description="Export format: 'json' or 'csv'")
    include_audit_trail: bool = Field(default=True, description="Whether to include audit logs")
    start_date: Optional[datetime] = Field(default=None, description="Start date filter for events")
    end_date: Optional[datetime] = Field(default=None, description="End date filter for events")


class ExportMetadata(BaseModel):
    standard: str = "GDPR Article 20 / CCPA Data Portability Compliant"
    generated_at: str
    user_id: int
    username: str
    event_count: int
    audit_log_count: int
    export_format: str


class ExportResponse(BaseModel):
    metadata: ExportMetadata
    active_permissions: Dict[str, bool]
    events: List[Dict[str, Any]]
    audit_trail: Optional[List[Dict[str, Any]]] = None
