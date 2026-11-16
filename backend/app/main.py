import os
import http
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings, ROOT_DIR
from app.core.database import engine, Base, SessionLocal
from app.api import api_router
from app.models.user import User
from app.services.privacy_service import PrivacyService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)
    
    # Ensure seeded demo user exists
    db = SessionLocal()
    try:
        demo_user = db.query(User).filter(User.id == settings.DEFAULT_USER_ID).first()
        if not demo_user:
            demo_user = User(
                id=settings.DEFAULT_USER_ID,
                name="Alex River (Demo User)",
                email="demo.user@chronis.ai"
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        # Ensure default permissions exist
        PrivacyService.ensure_default_permissions(db, demo_user.id)
    finally:
        db.close()
    
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Privacy-aware memory timeline backend for Chronis SDE Intern evaluation.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Transforms Pydantic validation failures into clear, structured, sensible error responses.
    """
    errors = []
    error_messages = []
    for err in exc.errors():
        loc_str = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        errors.append({
            "field": loc_str,
            "message": msg,
            "type": err.get("type", "value_error")
        })
        error_messages.append(f"{loc_str}: {msg}")
    
    summary = "; ".join(error_messages)
    return JSONResponse(
        status_code=422,
        content={
            "status_code": 422,
            "error": "Unprocessable Entity",
            "message": f"Validation failed: {summary}",
            "detail": summary,
            "errors": errors
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Standardizes HTTP error responses across the application.
    """
    try:
        phrase = http.HTTPStatus(exc.status_code).phrase
    except ValueError:
        phrase = "Error"
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error": phrase,
            "message": str(exc.detail),
            "detail": str(exc.detail)
        }
    )


# Include both root-level endpoints and versioned endpoints
app.include_router(api_router)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


# Mount frontend static files (served at /)
frontend_dir = os.path.join(ROOT_DIR, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
