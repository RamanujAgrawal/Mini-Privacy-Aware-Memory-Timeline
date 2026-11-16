import pytest


def test_create_and_fetch_event(client):
    """
    Requirements:
    - Create and fetch an event.
    - An event should contain at least: id, user_id, timestamp, type, title, content.
    """
    payload = {
        "type": "conversation",
        "title": "Discussion with engineering lead",
        "content": "Discussed system architecture and privacy models."
    }
    # 1. Create event
    response = client.post("/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["content"] == payload["content"]
    assert data["type"] == "conversation"
    assert data["user_id"] == 1
    assert "id" in data
    assert "timestamp" in data
    event_id = data["id"]

    # 2. Fetch event
    fetch_resp = client.get(f"/events/{event_id}")
    assert fetch_resp.status_code == 200
    fetch_data = fetch_resp.json()
    assert fetch_data["id"] == event_id
    assert fetch_data["title"] == payload["title"]
    assert fetch_data["type"] == "conversation"


def test_delete_event(client):
    """
    Test deleting an event and verifying it no longer exists.
    """
    # Create event first
    create_resp = client.post("/events", json={
        "type": "note",
        "title": "Temporary note",
        "content": "Delete me soon"
    })
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    # Delete event
    del_resp = client.delete(f"/events/{event_id}")
    assert del_resp.status_code == 200

    # Verify not found
    get_resp = client.get(f"/events/{event_id}")
    assert get_resp.status_code == 404


def test_event_validation_errors(client):
    """
    Test input validation on event creation (empty title, invalid category).
    """
    # Empty title
    bad_payload = {
        "type": "conversation",
        "title": "   ",
        "content": "Valid content"
    }
    resp = client.post("/events", json=bad_payload)
    assert resp.status_code == 422

    # Invalid type
    invalid_type_payload = {
        "type": "super_secret_category",
        "title": "Valid title",
        "content": "Valid content"
    }
    resp2 = client.post("/events", json=invalid_type_payload)
    assert resp2.status_code == 422
