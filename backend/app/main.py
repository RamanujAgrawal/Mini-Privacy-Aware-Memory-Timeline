import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
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
# Location: project_root/frontend
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
frontend_dir = os.path.join(base_dir, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
