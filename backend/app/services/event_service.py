import re
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.models.event import Event
from app.models.privacy_rule import PrivacyRule
from app.schemas.event import EventCreate
from app.services.privacy_service import PrivacyService
from app.services.audit_service import AuditService


class EventService:
    @staticmethod
    def create_event(db: Session, user_id: int, event_in: EventCreate) -> Event:
        """
        Creates and stores a new event for the user, logging the creation.
        """
        ts = event_in.timestamp or datetime.now(timezone.utc)
        event = Event(
            user_id=user_id,
            timestamp=ts,
            type=event_in.type.value if hasattr(event_in.type, "value") else str(event_in.type),
            title=event_in.title,
            content=event_in.content
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        AuditService.record_action(
            db=db,
            user_id=user_id,
            action="CREATE_EVENT",
            result="CREATED",
            event_type=event.type
        )
        return event

    @staticmethod
    def apply_privacy_rules(db: Session, user_id: int, event: Event) -> Optional[Event]:
        """
        Applies granular privacy rules (keyword redaction, pattern filtering).
        Returns the event (potentially with redacted content), or None if dropped.
        """
        rules = db.query(PrivacyRule).filter(
            PrivacyRule.user_id == user_id,
            PrivacyRule.is_enabled == True,
            or_(PrivacyRule.category == event.type, PrivacyRule.category == "all")
        ).all()

        if not rules:
            return event

        content = event.content
        was_redacted = False

        for rule in rules:
            pattern = rule.pattern.strip()
            if not pattern:
                continue

            # Check if pattern matches in title or content
            match = re.search(re.escape(pattern), content, re.IGNORECASE) or re.search(re.escape(pattern), event.title, re.IGNORECASE)
            if match:
                if rule.action == "drop":
                    AuditService.record_action(
                        db=db,
                        user_id=user_id,
                        action="PRIVACY_RULE_DROP",
                        result="DENIED",
                        event_type=event.type
                    )
                    return None
                elif rule.action in ("redact", "mask"):
                    content = re.sub(re.escape(pattern), "[REDACTED BY PRIVACY RULE]", content, flags=re.IGNORECASE)
                    was_redacted = True

        if was_redacted:
            # Return an in-memory modified event copy so database is not permanently corrupted
            redacted_event = Event(
                id=event.id,
                user_id=event.user_id,
                timestamp=event.timestamp,
                type=event.type,
                title=event.title,
                content=content
            )
            AuditService.record_action(
                db=db,
                user_id=user_id,
                action="PRIVACY_RULE_REDACT",
                result="ALLOWED_REDACTED",
                event_type=event.type
            )
            return redacted_event

        return event

    @staticmethod
    def get_events(
        db: Session,
        user_id: int,
        type_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_query: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Event], int]:
        """
        Retrieves events respecting user privacy permissions, date ranges, and full-text search.
        Applies automated granular privacy rules (redaction/drop).
        """
        allowed_categories = PrivacyService.get_allowed_categories(db, user_id)

        # If user explicitly filtered by a category that is disabled, return empty
        if type_filter:
            if type_filter not in allowed_categories:
                AuditService.record_action(
                    db=db,
                    user_id=user_id,
                    action="GET_EVENTS_FILTERED",
                    result="DENIED",
                    event_type=type_filter
                )
                return [], 0
            query = db.query(Event).filter(Event.user_id == user_id, Event.type == type_filter)
        else:
            if not allowed_categories:
                AuditService.record_action(
                    db=db,
                    user_id=user_id,
                    action="GET_EVENTS",
                    result="ALLOWED_EMPTY_ALL_DISABLED",
                    event_type="all"
                )
                return [], 0
            query = db.query(Event).filter(Event.user_id == user_id, Event.type.in_(allowed_categories))

        # Date-range filtering
        if start_date:
            query = query.filter(Event.timestamp >= start_date)
        if end_date:
            query = query.filter(Event.timestamp <= end_date)

        # Full-text keyword search across title and content
        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(Event.title.ilike(term), Event.content.ilike(term))
            )

        total = query.count()
        raw_items = query.order_by(desc(Event.timestamp)).offset(offset).limit(limit).all()

        # Apply granular privacy rules
        processed_items = []
        for ev in raw_items:
            processed = EventService.apply_privacy_rules(db, user_id, ev)
            if processed is not None:
                processed_items.append(processed)

        AuditService.record_action(
            db=db,
            user_id=user_id,
            action="GET_EVENTS",
            result="ALLOWED",
            event_type=type_filter or "all_allowed"
        )
        return processed_items, total

    @staticmethod
    def get_event_by_id(db: Session, user_id: int, event_id: int) -> Event:
        """
        Retrieves a single event by ID. Enforces category permissions and privacy rules.
        """
        event = db.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found."
            )

        # Enforce category permission check
        if not PrivacyService.is_category_allowed(db, user_id, event.type):
            AuditService.record_action(
                db=db,
                user_id=user_id,
                action="GET_EVENT_DETAIL",
                result="DENIED",
                event_type=event.type
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to '{event.type}' events is restricted by your active privacy settings."
            )

        # Apply granular rules
        processed = EventService.apply_privacy_rules(db, user_id, event)
        if processed is None:
            AuditService.record_action(
                db=db,
                user_id=user_id,
                action="GET_EVENT_DETAIL",
                result="DENIED_RULE_DROP",
                event_type=event.type
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to event #{event_id} is restricted by an active granular privacy rule."
            )

        AuditService.record_action(
            db=db,
            user_id=user_id,
            action="GET_EVENT_DETAIL",
            result="ALLOWED",
            event_type=event.type
        )
        return processed

    @staticmethod
    def delete_event(db: Session, user_id: int, event_id: int) -> bool:
        """
        Deletes an event by ID and records a DELETED audit log.
        """
        event = db.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found."
            )

        event_type = event.type
        db.delete(event)
        db.commit()

        AuditService.record_action(
            db=db,
            user_id=user_id,
            action="DELETE_EVENT",
            result="DELETED",
            event_type=event_type
        )
        return True
