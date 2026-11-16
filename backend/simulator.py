"""
Chronis Real-Time Telemetry Simulator
Simulates a user's wearable / companion sensor feed by generating realistic events
and posting them to the Chronis backend API.

Usage:
    python backend/simulator.py               # Generates 1 event every 5 seconds
    python backend/simulator.py --once        # Generates a single batch of events
    python backend/simulator.py --count 5     # Generates 5 events and exits
"""
import sys
import os
import time
import random
import argparse
from datetime import datetime, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.event import EventCategory
from app.schemas.event import EventCreate
from app.services.event_service import EventService

SAMPLE_POOL = [
    # Conversation
    {
        "type": EventCategory.CONVERSATION,
        "title": "Strategy Discussion with Product Lead",
        "content": "Discussed privacy roadmap, user consent management, and audit log exports for Chronis 2.0."
    },
    {
        "type": EventCategory.CONVERSATION,
        "title": "Voice Note: Architecture Review",
        "content": "Summary of audio snippet: SQLite indexes provide sub-millisecond lookups for user timeline."
    },
    {
        "type": EventCategory.CONVERSATION,
        "title": "Coffee Catchup with Design Team",
        "content": "Reviewed minimal light-mode UI wireframes and micro-interaction tokens."
    },
    # Location
    {
        "type": EventCategory.LOCATION,
        "title": "Arrived at Coworking Hub",
        "content": "Location ping: 100 Montgomery St, Financial District. Geo-fence dwell time: 35 minutes."
    },
    {
        "type": EventCategory.LOCATION,
        "title": "Coffee Shop Transit Ping",
        "content": "Location ping: 398 4th St, SOMA, San Francisco, CA. Dwell time: 18 minutes."
    },
    {
        "type": EventCategory.LOCATION,
        "title": "Evening Walk along Embarcadero",
        "content": "Location ping: Pier 14 Promenade. Distance covered: 1.4 miles."
    },
    # Physiological
    {
        "type": EventCategory.PHYSIOLOGICAL,
        "title": "Heart Rate Fluctuation Alert",
        "content": "Resting heart rate measured at 74 BPM. Heart rate variability (HRV): 62ms."
    },
    {
        "type": EventCategory.PHYSIOLOGICAL,
        "title": "Active Workout Summary",
        "content": "Cardio session detected. Peak heart rate: 142 BPM. Total calories burned: 280 kcal."
    },
    {
        "type": EventCategory.PHYSIOLOGICAL,
        "title": "Recovery & Stress Level Score",
        "content": "Stress index: Low (18/100). Physiological recovery status optimal."
    },
    # Note
    {
        "type": EventCategory.NOTE,
        "title": "Quick Idea: Keyset Cursor Pagination",
        "content": "To scale past 1M events, keyset pagination using timestamp + id avoids offset scan overhead."
    },
    {
        "type": EventCategory.NOTE,
        "title": "Reading List: Data Privacy By Design",
        "content": "Look up Ann Cavoukian's 7 Foundational Principles of Privacy by Design."
    },
    {
        "type": EventCategory.NOTE,
        "title": "Reminder: Prepare Demo Recording",
        "content": "Walk through timeline, toggle permission OFF, probe 403 Forbidden, and show audit log."
    }
]


def generate_single_event(db, user_id=1):
    """Pick a random realistic event and insert it via EventService."""
    template = random.choice(SAMPLE_POOL)
    event_in = EventCreate(
        type=template["type"],
        title=template["title"],
        content=template["content"],
        timestamp=datetime.now(timezone.utc)
    )
    event = EventService.create_event(db=db, user_id=user_id, event_in=event_in)
    return event


def run_simulator(count=None, interval=5, user_id=1):
    db = SessionLocal()
    print("=" * 60)
    print("Chronis Wearable Telemetry Simulator Started")
    print(f"Target User ID: {user_id} | Interval: {interval}s")
    print("Press CTRL+C to stop simulation.")
    print("=" * 60)

    generated = 0
    try:
        while True:
            event = generate_single_event(db, user_id=user_id)
            generated += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Simulated #{event.id} [{event.type.upper()}]: {event.title}")

            if count and generated >= count:
                print(f"Completed simulation of {generated} events.")
                break

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chronis Telemetry Simulator")
    parser.add_argument("--count", type=int, default=None, help="Number of events to generate")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between generated events")
    parser.add_argument("--once", action="store_true", help="Generate 1 event and exit")
    parser.add_argument("--user-id", type=int, default=1, help="Target user ID")

    args = parser.parse_args()
    if args.once:
        run_simulator(count=1, interval=0, user_id=args.user_id)
    else:
        run_simulator(count=args.count, interval=args.interval, user_id=args.user_id)
