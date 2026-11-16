from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# In SQLite, multiple threads (such as FastAPI async workers) may interact with
# the same connection pool. Setting check_same_thread=False allows worker threads
# to safely share the pool without raising thread-access exceptions.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Session factory for generating independent database sessions per request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base model from which all SQLAlchemy entities inherit
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session for a single HTTP request.
    The try-finally block guarantees that the connection is closed back to the pool
    even if an unhandled exception or early return occurs during route execution.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
