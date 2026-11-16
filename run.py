"""
Entry point to run the Chronis Privacy Timeline server.
Usage:
    python run.py
"""
import sys
import os
import uvicorn

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.core.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Chronis Privacy Timeline Server...")
    print(f"API & UI URL:  http://{settings.HOST}:{settings.PORT}")
    print(f"API Docs URL:  http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 60)
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
