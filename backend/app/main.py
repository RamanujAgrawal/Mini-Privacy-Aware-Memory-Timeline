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
    # Safe lightweight SQLite migration for added columns
    if settings.DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                res = conn.execute(text("PRAGMA table_info(users)"))
                cols = [r[1] for r in res.fetchall()]
                if cols and "hashed_password" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)"))
                if cols and "is_active" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                conn.commit()
        except Exception:
            pass

    # Create all tables on startup
    Base.metadata.create_all(bind=engine)

    # Ensure high-performance composite indexes are created in SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_user_timestamp ON events(user_id, timestamp)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_user_type_timestamp ON events(user_id, type, timestamp)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_timestamp ON audit_logs(user_id, timestamp)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_privacy_rules_user_enabled ON privacy_rules(user_id, is_enabled)"))
                conn.commit()
        except Exception:
            pass
    
    # Ensure seeded demo user exists
    db = SessionLocal()
    try:
        demo_user = db.query(User).filter(User.id == settings.DEFAULT_USER_ID).first()
        if not demo_user:
            demo_user = User(
                id=settings.DEFAULT_USER_ID,
                name="Demo User",
                email="demo.user@chronis.ai"
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        elif demo_user.name != "Demo User":
            demo_user.name = "Demo User"
            db.commit()
        # Ensure default permissions exist
        PrivacyService.ensure_default_permissions(db, demo_user.id)
    finally:
        db.close()
    
    yield


API_DESCRIPTION = """
### Chronis • Privacy-Aware Memory Timeline API

A production-grade, privacy-first backend built for wearable AI companion devices.

---

### Core Security & Privacy Invariants

1. **SQL-Level Category Elimination (`GET /events`)**:
   - Disabled categories are eliminated directly in database queries (`WHERE type IN (...)`).
   - Restricted records are **never loaded into server RAM** or sent over the wire.

2. **Single-Resource 403 Forbidden Guard (`GET /events/{id}`)**:
   - Direct requests for events belonging to disabled categories are rejected with **`HTTP 403 Forbidden`**.
   - An immutable forensic audit entry is atomically written with `result: "DENIED"`.

3. **Read-Only Immutable Audit Trail (`GET /audit-log`)**:
   - Records every event creation, deletion, permission toggle, allowed access, and blocked attempt.
   - Any attempt to mutate or delete logs via `POST`, `PUT`, or `DELETE` returns `HTTP 405 Method Not Allowed`.

---

### Interactive Swagger UI Testing Guide

Use this interactive console to test and verify privacy boundaries in real time:

* **Step 1: Inspect Default Permitted Timeline**
  - Go to `GET /events` below and click **Execute**.
  - Observe that all 4 categories (`conversation`, `location`, `physiological`, `note`) are returned.

* **Step 2: Toggle a Category to OFF**
  - Go to `PUT /permissions` below.
  - Set `category: "location"` and `is_enabled: false`, then click **Execute**.

* **Step 3: Verify SQL-Level Filtering**
  - Return to `GET /events` and click **Execute**.
  - Notice that all `location` records are completely excluded from the result set!

* **Step 4: Probe Direct Access & Observe 403 Forbidden**
  - Go to `GET /events/{event_id}`.
  - Enter the ID of a location event (e.g. `3`) and click **Execute**.
  - The backend returns `403 Forbidden` with `"Access to 'location' events is restricted by your active privacy settings"`.

* **Step 5: Verify the Audit Trail**
  - Go to `GET /audit-log` and click **Execute**.
  - Notice the recorded `PERMISSION_SET_OFF` and `DENIED` entries with timestamps.

* **Step 6: Test GDPR / CCPA Data Portability Export**
  - Go to `POST /export` with `{"format": "json", "include_audit_trail": true}` or `{"format": "csv"}`.
  - Notice that exported data strictly respects your active privacy settings.

---

### Quick Navigation Links

* 🖥️ **[Launch Web Timeline UI](/)** — Visual frontend application with real-time wearable simulator.
* 🎥 **[Interactive Demo Video (2:35)](/demo_video.html)** — Full HD narrated walkthrough with chapters and audio narration.
* 📖 **[ReDoc API Documentation](/redoc)** — Clean, responsive specification-driven API viewer.
* 📦 **[OpenAPI JSON Specification](/openapi.json)** — Raw OpenAPI v3.1 schema.
"""

TAGS_METADATA = [
    {
        "name": "Events",
        "description": "Core memory timeline operations. Enforces SQL query-level elimination of disabled categories and returns HTTP 403 Forbidden for restricted direct lookups.",
    },
    {
        "name": "Privacy Permissions",
        "description": "Category toggle controls (`conversation`, `location`, `physiological`, `note`). Dynamically alters access boundaries and writes audit entries.",
    },
    {
        "name": "Audit Log",
        "description": "Immutable, read-only forensic audit trail. Every create, delete, permission toggle, allowed access, and blocked attempt is permanently recorded.",
    },
    {
        "name": "Authentication & Multi-Tenancy",
        "description": "User registration, PBKDF2 password verification, and JWT Bearer token generation. Provides tenant data isolation across accounts.",
    },
    {
        "name": "Granular Privacy Rules",
        "description": "Rule-based privacy automation. Supports keyword redactions (`[REDACTED BY PRIVACY RULE]`) and pattern drop actions.",
    },
    {
        "name": "Export & Data Portability",
        "description": "GDPR Article 20 and CCPA data portability export in structured JSON or downloadable CSV format.",
    },
    {
        "name": "System",
        "description": "Service health check, uptime, and system diagnostic endpoints.",
    },
]

SWAGGER_UI_PARAMETERS = {
    "filter": True,                  # Instant search bar to filter endpoints
    "tryItOutEnabled": True,         # Expands Try-it-out section automatically for 1-click execution
    "displayRequestDuration": True,  # Displays latency (e.g. Duration: 1.4ms) under each response
    "persistAuthorization": True,    # Keeps Bearer token stored across page refreshes
    "defaultModelsExpandDepth": -1,  # Keeps models collapsed for cleaner visual focus
    "docExpansion": "list",          # Expands tag groups cleanly
}


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=API_DESCRIPTION,
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
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
