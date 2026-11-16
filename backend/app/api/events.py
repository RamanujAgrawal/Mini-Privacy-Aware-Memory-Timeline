from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.event import EventCreate, EventResponse, EventListResponse
from app.services.event_service import EventService

router = APIRouter(tags=["Events"])


@router.get(
    "/events",
    response_model=EventListResponse,
    summary="List events with privacy filtering and pagination"
)
def list_events(
    type: Optional[str] = Query(None, description="Filter events by category (conversation, location, physiological, note)"),
    limit: int = Query(20, ge=1, le=100, description="Max number of items to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Returns events for the active user in descending chronological order.
    Categories turned OFF in user privacy settings are strictly omitted.
    """
    items, total = EventService.get_events(
        db=db,
        user_id=user_id,
        type_filter=type,
        limit=limit,
        offset=offset
    )
    return EventListResponse(
        items=[EventResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/events/{event_id}",
    response_model=EventResponse,
    summary="Get a single event by ID"
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Fetches a specific event by ID.
    If the event belongs to a disabled privacy category, an HTTP 403 Forbidden
    is returned and a DENIED record is saved to the audit log.
    """
    event = EventService.get_event_by_id(db=db, user_id=user_id, event_id=event_id)
    return EventResponse.model_validate(event)


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event"
)
def create_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Records a new memory event for the user.
    """
    event = EventService.create_event(db=db, user_id=user_id, event_in=event_in)
    return EventResponse.model_validate(event)


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an event by ID"
)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Deletes an event by ID and records a DELETED entry in the audit log.
    """
    EventService.delete_event(db=db, user_id=user_id, event_id=event_id)
    return {"status": "success", "message": f"Event {event_id} deleted successfully."}
