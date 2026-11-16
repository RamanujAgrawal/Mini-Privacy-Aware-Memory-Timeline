from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models.event import EventCategory


class EventBase(BaseModel):
    type: EventCategory
    title: str = Field(..., min_length=1, max_length=255, description="Title of the event")
    content: str = Field(..., min_length=1, description="Content/description of the event")
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Optional ISO timestamp; defaults to now (UTC) if omitted"
    )

    @field_validator("title", "content")
    @classmethod
    def not_empty_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or only whitespace")
        return v.strip()


class EventCreate(EventBase):
    pass


class EventResponse(BaseModel):
    id: int
    user_id: int
    timestamp: datetime
    type: str
    title: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    items: List[EventResponse]
    total: int
    limit: int
    offset: int
