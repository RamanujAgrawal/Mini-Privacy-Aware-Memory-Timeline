from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.event import EventCreate, EventResponse, EventListResponse
from app.schemas.error import ErrorResponse, ValidationErrorResponse
from app.services.event_service import EventService

router = APIRouter(tags=["Events"])


def _parse_datetime_query(val: Optional[str]) -> Optional[datetime]:
    """
    Safely parses query parameter strings into datetime objects.
    Handles URL-encoded '+' offsets (which often decode as spaces in query strings).
    """
    if not val:
        return None
    cleaned = val.strip().replace(" ", "+")
    try:
        return datetime.fromisoformat(cleaned)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid datetime format: '{val}'. Expected ISO 8601 string (e.g., 2026-11-16T10:00:00Z)."
        )


@router.get(
    "/events",
    response_model=EventListResponse,
    summary="List events with privacy filtering, search, date-range, and pagination",
    responses={
        200: {"description": "Events retrieved successfully (restricted categories strictly omitted at SQL level)."},
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error: invalid query parameters (e.g., limit < 1 or invalid category name)."
        }
    }
)
def list_events(
    type: Optional[str] = Query(None, description="Filter events by category (conversation, location, physiological, note)"),
    start_date: Optional[str] = Query(None, description="Filter events on or after this timestamp (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Filter events on or before this timestamp (ISO 8601)"),
    q: Optional[str] = Query(None, description="Full-text search query across event title and content"),
    limit: int = Query(20, ge=1, le=100, description="Max number of items to return (1-100)"),
    offset: int = Query(0, ge=0, description="Pagination offset (>= 0)"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Returns events for the active user in descending chronological order.
    Categories turned OFF in user privacy settings are strictly omitted.
    Supports full-text keyword search, date-range filtering, and pagination.
    """
    parsed_start = _parse_datetime_query(start_date)
    parsed_end = _parse_datetime_query(end_date)

    items, total = EventService.get_events(
        db=db,
        user_id=user_id,
        type_filter=type,
        start_date=parsed_start,
        end_date=parsed_end,
        search_query=q,
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
    summary="Get a single event by ID",
    responses={
        200: {"description": "Event details retrieved successfully."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden: Access restricted by active user privacy settings (generates a DENIED audit entry)."
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found: The requested event ID does not exist for this user."
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error: event_id must be a valid integer."
        }
    }
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
    summary="Create a new event",
    responses={
        201: {"description": "Event created and indexed successfully."},
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error: title or content cannot be empty whitespace, and category must be valid."
        }
    }
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
    summary="Delete an event by ID",
    responses={
        200: {"description": "Event successfully deleted from user's timeline."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found: The event ID does not exist."
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error: event_id must be an integer."
        }
    }
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
