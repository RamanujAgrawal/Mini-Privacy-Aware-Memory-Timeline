from fastapi import APIRouter
from app.api.events import router as events_router
from app.api.permissions import router as permissions_router
from app.api.audit_log import router as audit_log_router

api_router = APIRouter()
api_router.include_router(events_router)
api_router.include_router(permissions_router)
api_router.include_router(audit_log_router)
