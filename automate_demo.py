"""
Chronis Automated Evaluation & Verification Runner
Demonstrates the full end-to-end privacy workflow, authorization enforcement,
and automated test suite execution in a single automated run.

Usage:
    python automate_demo.py
"""
import sys
import os
import subprocess
from datetime import datetime

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.services.privacy_service import PrivacyService

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_step(step_num, title):
    print(f"\n{BOLD}{CYAN}[Step {step_num}]{RESET} {BOLD}{title}{RESET}")
    print("-" * 65)


def assert_success(condition, message):
    if condition:
        print(f"  {GREEN}✓ PASS:{RESET} {message}")
    else:
        print(f"  {RED}✗ FAIL:{RESET} {message}")
        sys.exit(1)


def run_automated_demo():
    print(f"{BOLD}{BLUE}================================================================={RESET}")
    print(f"{BOLD}{BLUE}    CHRONIS • AUTOMATED PRIVACY TIMELINE VERIFICATION RUNNER    {RESET}")
    print(f"{BOLD}{BLUE}================================================================={RESET}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target DB: SQLite (Repository Root)\n")

    # 1. Setup client
    client = TestClient(app)

    # Step 1: Health & System Check
    print_step(1, "Service Health & API Docs Verification")
    health = client.get("/health")
    assert_success(health.status_code == 200, f"Health check returned 200 OK: {health.json()['status']}")
    
    docs = client.get("/openapi.json")
    assert_success(docs.status_code == 200, f"OpenAPI schema generated successfully ({len(docs.json()['paths'])} endpoints)")

    # Step 2: Check Initial Permissions (All 4 categories ON)
    print_step(2, "Verifying Default Privacy Permissions")
    perms_res = client.get("/permissions")
    assert_success(perms_res.status_code == 200, "GET /permissions returned 200 OK")
    perms = perms_res.json()["permissions"]
    for cat in ["conversation", "location", "physiological", "note"]:
        assert_success(perms.get(cat) is True, f"Category '{cat}' is initially active (ON)")

    # Step 3: Ingest Events Across Categories
    print_step(3, "Creating Memory Events across all 4 Categories")
    sample_events = [
        {"type": "conversation", "title": "Lead Sync", "content": "Discussed privacy architecture."},
        {"type": "location", "title": "Coffee Shop Ping", "content": "Lat: 37.78, Long: -122.40"},
        {"type": "physiological", "title": "Heart Rate Peak", "content": "112 BPM during morning run"},
        {"type": "note", "title": "System Reminder", "content": "Review GDPR data subject rights."}
    ]
    created_ids = {}
    for ev in sample_events:
        res = client.post("/events", json=ev)
        assert_success(res.status_code == 201, f"Created {ev['type']} event #{res.json()['id']}")
        created_ids[ev["type"]] = res.json()["id"]

    location_event_id = created_ids["location"]

    # Step 4: Verify Initial Event Retrieval
    print_step(4, "Verifying Events are Returned when Categories are ON")
    list_res = client.get("/events")
    items = list_res.json()["items"]
    types_found = {item["type"] for item in items}
    assert_success("location" in types_found, "Location event is visible in timeline")
    
    direct_loc = client.get(f"/events/{location_event_id}")
    assert_success(direct_loc.status_code == 200, f"Direct GET /events/{location_event_id} allowed (HTTP 200 OK)")

    # Step 5: Toggle Privacy Permission OFF (Location)
    print_step(5, "Toggling 'location' Permission to OFF via API")
    put_res = client.put("/permissions", json={"category": "location", "is_enabled": False})
    assert_success(put_res.status_code == 200, "PUT /permissions returned 200 OK")
    assert_success(put_res.json()["is_enabled"] is False, "Permission successfully set to False")

    # Step 6: Verify Backend Omits Location Events
    print_step(6, "Verifying GET /events Strictly Excludes Disabled Category")
    after_list = client.get("/events")
    after_items = after_list.json()["items"]
    after_types = {item["type"] for item in after_items}
    assert_success("location" not in after_types, "Backend strictly excluded all 'location' data from collection query")
    assert_success(not any(it["id"] == location_event_id for it in after_items), f"Event #{location_event_id} is completely omitted from response")

    # Step 7: Probe Direct Access & Assert 403 Forbidden
    print_step(7, "Probing Direct Access: GET /events/{id} on Restricted Category")
    direct_blocked = client.get(f"/events/{location_event_id}")
    assert_success(direct_blocked.status_code == 403, f"Direct access correctly rejected with HTTP 403 Forbidden")
    assert_success("restricted by your active privacy settings" in direct_blocked.json()["detail"], 
                   f"Descriptive rejection message: \"{direct_blocked.json()['detail']}\"")

    # Step 8: Verify Read-Only Audit Log
    print_step(8, "Verifying Audit Log Trail Recorded Actions & DENIED Result")
    audit_res = client.get("/audit-log")
    assert_success(audit_res.status_code == 200, "GET /audit-log returned 200 OK")
    audit_items = audit_res.json()["items"]
    actions = [a["action"] for a in audit_items]
    results = [a["result"] for a in audit_items]

    assert_success("PERMISSION_SET_OFF" in actions, "Audit trail logged 'PERMISSION_SET_OFF'")
    assert_success("DENIED" in results, "Audit trail logged security 'DENIED' entry for blocked access attempt")

    # Verify audit log is read-only
    tamper_res = client.post("/audit-log", json={"action": "MALICIOUS"})
    assert_success(tamper_res.status_code in (404, 405), "Audit log mutation blocked (Read-Only enforcement verified)")

    # Step 9: Re-enable Permission
    print_step(9, "Restoring 'location' Permission to ON")
    restore_res = client.put("/permissions", json={"category": "location", "is_enabled": True})
    assert_success(restore_res.status_code == 200, "Permission restored to True")
    
    restored_get = client.get(f"/events/{location_event_id}")
    assert_success(restored_get.status_code == 200, f"Event #{location_event_id} is immediately accessible again (HTTP 200 OK)")

    # Step 10: Run Automated Pytest Suite
    print_step(10, "Executing Full Automated Pytest Test Suite")
    pytest_cmd = [sys.executable, "-m", "pytest", os.path.join(BASE_DIR, "backend", "tests"), "-v"]
    print(f"Running: {' '.join(pytest_cmd)}")
    result = subprocess.run(pytest_cmd, capture_output=True, text=True)
    print(result.stdout)
    assert_success(result.returncode == 0, "All automated unit and integration tests passed!")

    print(f"\n{BOLD}{GREEN}================================================================={RESET}")
    print(f"{BOLD}{GREEN}    ALL AUTOMATED PRIVACY VERIFICATIONS COMPLETED SUCCESSFULLY!  {RESET}")
    print(f"{BOLD}{GREEN}================================================================={RESET}\n")


if __name__ == "__main__":
    run_automated_demo()
