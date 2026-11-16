from datetime import datetime, timezone
from typing import Optional, List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.event import Event
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

        # Audit log creation
        AuditService.record_action(
            db=db,
            user_id=user_id,
            action="CREATE_EVENT",
            result="CREATED",
            event_type=event.type
        )
        return event

    @staticmethod
    def get_events(
        db: Session,
        user_id: int,
        type_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Event], int]:
        """
        Retrieves events respecting the user's active privacy permissions.
        Events whose category is turned OFF are strictly omitted at query level.
        Supports pagination and type filtering.
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
            
            # Query only this specific allowed category
            query = db.query(Event).filter(
                Event.user_id == user_id,
                Event.type == type_filter
            )
        else:
            # Query all allowed categories
            if not allowed_categories:
                AuditService.record_action(
                    db=db,
                    user_id=user_id,
                    action="GET_EVENTS",
                    result="ALLOWED_EMPTY_ALL_DISABLED",
                    event_type="all"
                )
                return [], 0

            query = db.query(Event).filter(
                Event.user_id == user_id,
                Event.type.in_(allowed_categories)
            )

        total = query.count()
        items = query.order_by(desc(Event.timestamp)).offset(offset).limit(limit).all()

        AuditService.record_action(
            db=db,
            user_id=user_id,
            action="GET_EVENTS",
            result="ALLOWED",
            event_type=type_filter or "all_allowed"
        )
        return items, total

    @staticmethod
    def get_event_by_id(db: Session, user_id: int, event_id: int) -> Event:
        """
        Retrieves a single event by ID.
        If category is disabled by privacy settings, raises HTTP 403 Forbidden
        and records a DENIED audit log entry.
        """
        event = db.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found."
            )

        # Enforce privacy check
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

        AuditService.record_action(
            db=db,
            user_id=user_id,
            action="GET_EVENT_DETAIL",
            result="ALLOWED",
            event_type=event.type
        )
        return event

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
