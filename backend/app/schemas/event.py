from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, field_serializer, ConfigDict
from app.models.event import EventCategory


class EventBase(BaseModel):
    """
    Shared attributes for memory event ingestion.
    """
    type: EventCategory = Field(..., description="Category: conversation, location, physiological, note")
    title: str = Field(..., min_length=1, max_length=255, description="Brief title summarizing the event")
    content: str = Field(..., min_length=1, description="Event body, transcript, coordinates, or notes")
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Optional ISO 8601 timestamp; automatically defaults to UTC now if omitted"
    )

    @field_validator("title", "content")
    @classmethod
    def not_empty_whitespace(cls, v: str) -> str:
        """
        Guarantees that titles and contents are not merely empty strings or whitespace.
        """
        if not v.strip():
            raise ValueError("Field cannot be empty or only whitespace")
        return v.strip()


class EventCreate(EventBase):
    """Payload for POST /events."""
    pass


class EventResponse(BaseModel):
    """
    Public representation of a single memory event.
    """
    id: int
    user_id: int
    timestamp: datetime
    type: str
    title: str
    content: str

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime, _info) -> str:
        """
        SQLite stores datetimes without explicit timezone offsets.
        This serializer explicitly attaches UTC timezone info so the returned
        ISO 8601 string ends with '+00:00', preventing browser JavaScript engines
        from mistakenly parsing UTC strings as local time.
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    """
    Paginated collection response for GET /events.
    """
    items: List[EventResponse]
    total: int
    limit: int
    offset: int
