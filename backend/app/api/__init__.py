from fastapi import APIRouter
from app.api.events import router as events_router
from app.api.permissions import router as permissions_router
from app.api.audit_log import router as audit_log_router
from app.api.auth import router as auth_router
from app.api.privacy_rules import router as privacy_rules_router
from app.api.export import router as export_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(events_router)
api_router.include_router(permissions_router)
api_router.include_router(audit_log_router)
api_router.include_router(privacy_rules_router)
api_router.include_router(export_router)
