import pytest
from datetime import datetime, timezone, timedelta
from app.models.event import EventCategory


def test_auth_registration_and_login(client):
    """Approach 1: Verify JWT user registration, login, and protected /auth/me profile access."""
    reg_resp = client.post("/auth/register", json={
        "name": "Alice Springs",
        "email": "alice@example.com",
        "password": "StrongPassword123!"
    })
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["email"] == "alice@example.com"
    token = reg_data["access_token"]

    # Verify protected /auth/me with Bearer token
    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["name"] == "Alice Springs"

    # Test login with valid credentials
    login_resp = client.post("/auth/login", json={
        "email": "alice@example.com",
        "password": "StrongPassword123!"
    })
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # Test login with invalid password
    bad_login = client.post("/auth/login", json={
        "email": "alice@example.com",
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401


def test_multi_tenancy_data_isolation(client):
    """Approach 1: Verify multi-tenancy isolation between two distinct user accounts."""
    # Register User A
    u1_resp = client.post("/auth/register", json={
        "name": "User Alpha",
        "email": "alpha@example.com",
        "password": "Password123!"
    }).json()
    token_a = u1_resp["access_token"]

    # Register User B
    u2_resp = client.post("/auth/register", json={
        "name": "User Beta",
        "email": "beta@example.com",
        "password": "Password123!"
    }).json()
    token_b = u2_resp["access_token"]

    # User A creates an event
    ev_a = client.post(
        "/events",
        json={"type": "note", "title": "Alpha Secret Note", "content": "Restricted to Alpha"},
        headers={"Authorization": f"Bearer {token_a}"}
    ).json()
    ev_a_id = ev_a["id"]

    # User B queries /events
    events_b = client.get("/events", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert len(events_b["items"]) == 0

    # User B attempts direct retrieval of User A's event
    direct_resp = client.get(f"/events/{ev_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert direct_resp.status_code == 404


def test_date_range_and_fulltext_search(client):
    """Approach 2: Verify date-range filtering (start_date, end_date) and full-text keyword search (q)."""
    now = datetime.now(timezone.utc)
    d1 = (now - timedelta(days=10)).isoformat()
    d2 = (now - timedelta(days=5)).isoformat()
    d3 = now.isoformat()

    client.post("/events", json={"type": "note", "title": "Old Medical Note", "content": "Blood pressure check", "timestamp": d1})
    client.post("/events", json={"type": "conversation", "title": "Recent Team Sync", "content": "Quarterly planning and sprint review", "timestamp": d2})
    client.post("/events", json={"type": "location", "title": "City Hospital", "content": "Cardiology clinic visit", "timestamp": d3})

    # Test full-text keyword search on 'Cardiology'
    search_resp = client.get("/events?q=Cardiology")
    assert search_resp.status_code == 200
    data = search_resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "City Hospital"

    # Test full-text keyword search on 'sprint'
    search_resp2 = client.get("/events?q=sprint")
    assert search_resp2.status_code == 200
    assert search_resp2.json()["total"] == 1
    assert "Recent Team Sync" in search_resp2.json()["items"][0]["title"]

    # Test date-range filtering: events between d2-1day and d2+1day
    s_date = (now - timedelta(days=6)).isoformat()
    e_date = (now - timedelta(days=4)).isoformat()
    range_resp = client.get(f"/events?start_date={s_date}&end_date={e_date}")
    assert range_resp.status_code == 200
    assert range_resp.json()["total"] == 1
    assert range_resp.json()["items"][0]["title"] == "Recent Team Sync"


def test_granular_privacy_rules_redaction_and_drop(client):
    """Approach 3: Verify automated keyword redaction and rule drop actions."""
    # 1. Create a keyword redaction rule for 'secret_project' in conversation
    rule1_resp = client.post("/privacy-rules", json={
        "category": "conversation",
        "rule_type": "keyword_redact",
        "pattern": "secret_project",
        "action": "redact"
    })
    assert rule1_resp.status_code == 201
    rule1_id = rule1_resp.json()["id"]

    # Create a conversation event containing the keyword
    ev1 = client.post("/events", json={
        "type": "conversation",
        "title": "Meeting Transcript",
        "content": "Discussing the secret_project roadmap."
    }).json()

    # Query events list -> should have redacted content
    res_list = client.get("/events?type=conversation").json()
    ev_item = [x for x in res_list["items"] if x["id"] == ev1["id"]][0]
    assert "[REDACTED BY PRIVACY RULE]" in ev_item["content"]
    assert "secret_project" not in ev_item["content"]

    # 2. Create a drop rule for location with pattern 'Home'
    rule2_resp = client.post("/privacy-rules", json={
        "category": "location",
        "rule_type": "pattern_drop",
        "pattern": "Home",
        "action": "drop"
    })
    assert rule2_resp.status_code == 201

    ev2 = client.post("/events", json={
        "type": "location",
        "title": "Evening GPS",
        "content": "Arrived at Home address."
    }).json()

    # List events -> should be dropped
    loc_list = client.get("/events?type=location").json()
    loc_ids = [x["id"] for x in loc_list["items"]]
    assert ev2["id"] not in loc_ids

    # Direct retrieval -> should return 403 Forbidden
    direct_loc = client.get(f"/events/{ev2['id']}")
    assert direct_loc.status_code == 403

    # 3. Delete rule 1 and verify redaction is removed
    del_resp = client.delete(f"/privacy-rules/{rule1_id}")
    assert del_resp.status_code == 200

    refreshed_list = client.get("/events?type=conversation").json()
    refreshed_ev = [x for x in refreshed_list["items"] if x["id"] == ev1["id"]][0]
    assert "secret_project" in refreshed_ev["content"]


def test_export_and_data_portability(client):
    """Approach 4: Verify POST /export and GET /export under GDPR Article 20 / CCPA."""
    # Seed events
    client.post("/events", json={"type": "note", "title": "My Diary", "content": "Personal reflections"})
    client.post("/events", json={"type": "physiological", "title": "Resting Heart Rate", "content": "72 bpm"})

    # Test JSON export
    post_json = client.post("/export", json={"format": "json", "include_audit_trail": True})
    assert post_json.status_code == 200
    data = post_json.json()
    assert "metadata" in data
    assert data["metadata"]["standard"] == "GDPR Article 20 / CCPA Data Portability Compliant"
    assert "events" in data
    assert len(data["events"]) >= 2
    assert "audit_trail" in data
    assert "active_permissions" in data

    # Test CSV export
    post_csv = client.post("/export", json={"format": "csv", "include_audit_trail": True})
    assert post_csv.status_code == 200
    assert "text/csv" in post_csv.headers["content-type"]
    assert "--- TIMELINE EVENTS ---" in post_csv.text
    assert "--- AUDIT TRAIL LOGS ---" in post_csv.text
    assert "My Diary" in post_csv.text

    # Verify audit log recorded the export
    audit_resp = client.get("/audit-log")
    assert audit_resp.status_code == 200
    actions = [log["action"] for log in audit_resp.json()["items"]]
    assert "EXPORT_DATA" in actions
