import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class EventCategory(str, enum.Enum):
    CONVERSATION = "conversation"
    LOCATION = "location"
    PHYSIOLOGICAL = "physiological"
    NOTE = "note"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    type = Column(
        String(50),
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    # Composite B-tree indexes for high-speed chronological timeline queries and category slicing
    __table_args__ = (
        Index("ix_events_user_timestamp", "user_id", "timestamp"),
        Index("ix_events_user_type_timestamp", "user_id", "type", "timestamp"),
    )

    # Relationships
    user = relationship("User", back_populates="events")
