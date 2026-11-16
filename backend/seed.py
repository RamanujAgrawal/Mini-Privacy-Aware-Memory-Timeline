"""
Seed script to populate initial demo user and memory timeline events.
Run via: python backend/seed.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.event import Event, EventCategory
from app.models.permission import Permission
from app.services.privacy_service import PrivacyService
from app.services.audit_service import AuditService


def seed_database():
    print("Creating tables if not present...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed or get Demo User
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = User(
                id=1,
                name="Alex River",
                email="alex.river@chronis.ai"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created demo user: {user.name} (ID: {user.id})")
        else:
            print(f"Found existing demo user: {user.name} (ID: {user.id})")

        # 2. Ensure Permissions
        PrivacyService.ensure_default_permissions(db, user.id)
        print("Initialized default permissions (all ON).")

        # 3. Seed Events if none exist
        existing_count = db.query(Event).filter(Event.user_id == user.id).count()
        if existing_count == 0:
            now = datetime.now(timezone.utc)
            sample_events = [
                # Conversation events
                {
                    "type": EventCategory.CONVERSATION.value,
                    "title": "Morning Sync with Lead Architect",
                    "content": "Discussed privacy boundaries, event indexing strategy, and read-only audit log retention.",
                    "timestamp": now - timedelta(hours=7, minutes=30)
                },
                {
                    "type": EventCategory.CONVERSATION.value,
                    "title": "Coffee catchup with Sarah",
                    "content": "Talked about the upcoming Chronis hardware trial and sensor calibration benchmarks.",
                    "timestamp": now - timedelta(hours=3, minutes=15)
                },
                # Location events
                {
                    "type": EventCategory.LOCATION.value,
                    "title": "Arrived at Chronis HQ",
                    "content": "Location ping: 500 Howard St, San Francisco, CA 94105. Geo-fence entered.",
                    "timestamp": now - timedelta(hours=8, minutes=45)
                },
                {
                    "type": EventCategory.LOCATION.value,
                    "title": "Lunch at Blue Bottle Market",
                    "content": "Location ping: 66 Mint Plaza, San Francisco, CA. Dwell time: 42 minutes.",
                    "timestamp": now - timedelta(hours=4, minutes=30)
                },
                # Physiological events
                {
                    "type": EventCategory.PHYSIOLOGICAL.value,
                    "title": "Elevated Heart Rate Alert",
                    "content": "Resting heart rate peaked at 118 BPM during high intensity sprint session.",
                    "timestamp": now - timedelta(hours=6, minutes=10)
                },
                {
                    "type": EventCategory.PHYSIOLOGICAL.value,
                    "title": "Deep Sleep Summary",
                    "content": "Sleep duration: 7h 24m. Deep sleep: 1h 48m (24%). Recovery score: 88/100.",
                    "timestamp": now - timedelta(hours=10, minutes=0)
                },
                # Note events
                {
                    "type": EventCategory.NOTE.value,
                    "title": "Idea: Ephemeral Memory Buffer",
                    "content": "What if audio clips in conversations expire after 24 hours unless explicitly pinned by user?",
                    "timestamp": now - timedelta(hours=5, minutes=0)
                },
                {
                    "type": EventCategory.NOTE.value,
                    "title": "Book recommendations to review",
                    "content": "Designing Data-Intensive Applications (Kleppmann) and Privacy by Design guidelines.",
                    "timestamp": now - timedelta(hours=1, minutes=45)
                }
            ]

            for item in sample_events:
                ev = Event(
                    user_id=user.id,
                    type=item["type"],
                    title=item["title"],
                    content=item["content"],
                    timestamp=item["timestamp"]
                )
                db.add(ev)
            db.commit()
            print(f"Seeded {len(sample_events)} realistic timeline events.")

            # Record initial audit entry
            AuditService.record_action(
                db=db,
                user_id=user.id,
                action="SYSTEM_SEED_INITIAL_DATA",
                result="SUCCESS",
                event_type="all"
            )
        else:
            print(f"User already has {existing_count} events in database. Skipping seed.")

        print("Database seed complete!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
