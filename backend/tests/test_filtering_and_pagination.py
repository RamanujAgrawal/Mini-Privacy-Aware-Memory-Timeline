import pytest


def test_type_filtering(client):
    """
    Requirements:
    GET /events must support type filtering.
    """
    # Seed events across multiple categories
    events = [
        {"type": "conversation", "title": "Conv 1", "content": "Content 1"},
        {"type": "location", "title": "Loc 1", "content": "Content 2"},
        {"type": "physiological", "title": "Physio 1", "content": "Content 3"},
        {"type": "note", "title": "Note 1", "content": "Content 4"},
        {"type": "conversation", "title": "Conv 2", "content": "Content 5"}
    ]
    for ev in events:
        res = client.post("/events", json=ev)
        assert res.status_code == 201

    # Filter by conversation
    resp = client.get("/events?type=conversation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["type"] == "conversation"

    # Filter by location
    loc_resp = client.get("/events?type=location")
    assert loc_resp.status_code == 200
    loc_data = loc_resp.json()
    assert loc_data["total"] == 1
    assert loc_data["items"][0]["type"] == "location"


def test_pagination(client):
    """
    Requirements:
    GET /events must support pagination (limit, offset).
    """
    # Create 10 notes
    for i in range(10):
        client.post("/events", json={
            "type": "note",
            "title": f"Note #{i}",
            "content": f"Content for note {i}"
        })

    # Page 1: limit 4, offset 0
    page1 = client.get("/events?limit=4&offset=0")
    assert page1.status_code == 200
    data1 = page1.json()
    assert data1["limit"] == 4
    assert data1["offset"] == 0
    assert data1["total"] == 10
    assert len(data1["items"]) == 4

    # Page 2: limit 4, offset 4
    page2 = client.get("/events?limit=4&offset=4")
    assert page2.status_code == 200
    data2 = page2.json()
    assert len(data2["items"]) == 4

    # Verify distinct items between pages
    ids_page1 = {item["id"] for item in data1["items"]}
    ids_page2 = {item["id"] for item in data2["items"]}
    assert ids_page1.isdisjoint(ids_page2)
