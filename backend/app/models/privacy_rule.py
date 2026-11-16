from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class PrivacyRule(Base):
    __tablename__ = "privacy_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # conversation, location, physiological, note, all
    rule_type = Column(String(50), nullable=False, default="keyword_redact")  # keyword_redact, pattern_drop, threshold_redact
    pattern = Column(String(255), nullable=False)  # e.g., 'confidential', '>130', 'pin'
    action = Column(String(50), nullable=False, default="redact")  # redact, drop, mask
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Composite index for filtering active rules by user
    __table_args__ = (
        Index("ix_privacy_rules_user_enabled", "user_id", "is_enabled"),
    )

    # Relationships
    user = relationship("User", back_populates="privacy_rules")
