from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_serializer, ConfigDict
from app.models.event import EventCategory


class PrivacyRuleCreate(BaseModel):
    category: EventCategory = Field(..., description="Target category (conversation, location, physiological, note)")
    rule_type: str = Field(default="keyword_redact", description="Type: keyword_redact, threshold_redact, regex_mask")
    pattern: str = Field(..., min_length=1, max_length=255, description="Pattern, keyword, or threshold string")
    action: str = Field(default="redact", description="Action to take: redact (mask content), drop (filter out)")


class PrivacyRuleResponse(BaseModel):
    id: int
    user_id: int
    category: str
    rule_type: str
    pattern: str
    action: str
    is_enabled: bool
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


class PrivacyRuleListResponse(BaseModel):
    items: List[PrivacyRuleResponse]
    total: int
