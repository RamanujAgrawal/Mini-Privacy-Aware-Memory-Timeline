import pytest


def test_enabled_category_is_returned(client):
    """
    Verify that by default, all categories are enabled and return data.
    """
    client.post("/events", json={
        "type": "location",
        "title": "Home",
        "content": "Arrived home safely"
    })
    resp = client.get("/events")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert any(item["type"] == "location" for item in items)


def test_disabled_category_is_not_returned_by_backend(client):
    """
    Requirements:
    - If a user turns a category OFF, the backend must stop returning that category's data.
    - Do not only hide it in the frontend. We will test the API directly.
    """
    # 1. Create a physiological event and a note event
    physio_res = client.post("/events", json={
        "type": "physiological",
        "title": "Heart rate spike",
        "content": "130 BPM after stairs"
    })
    physio_id = physio_res.json()["id"]

    note_res = client.post("/events", json={
        "type": "note",
        "title": "General note",
        "content": "A simple note"
    })
    note_id = note_res.json()["id"]

    # 2. Verify both appear when enabled
    init_get = client.get("/events")
    init_types = {ev["type"] for ev in init_get.json()["items"]}
    assert "physiological" in init_types
    assert "note" in init_types

    # 3. Disable 'physiological' category
    perm_res = client.put("/permissions", json={
        "category": "physiological",
        "is_enabled": False
    })
    assert perm_res.status_code == 200
    assert perm_res.json()["is_enabled"] is False

    # 4. GET /events must NOT return physiological data
    after_get = client.get("/events")
    after_items = after_get.json()["items"]
    after_types = {ev["type"] for ev in after_items}
    assert "physiological" not in after_types
    assert "note" in after_types
    assert not any(ev["id"] == physio_id for ev in after_items)

    # 5. Direct GET /events/{id} for the disabled event MUST return 403 Forbidden
    direct_get = client.get(f"/events/{physio_id}")
    assert direct_get.status_code == 403
    assert "restricted by your active privacy settings" in direct_get.json()["detail"]


def test_changing_permission_affects_later_requests(client):
    """
    Requirements:
    - Changing a permission affects later requests dynamically.
    - Test toggling OFF then back ON.
    """
    # Create conversation event
    conv = client.post("/events", json={
        "type": "conversation",
        "title": "Private confidential call",
        "content": "Discussed sensitive roadmap features."
    }).json()
    conv_id = conv["id"]

    # Step 1: Accessible initially
    r1 = client.get(f"/events/{conv_id}")
    assert r1.status_code == 200

    # Step 2: Turn OFF
    client.put("/permissions", json={"category": "conversation", "is_enabled": False})

    # Now blocked
    r2_list = client.get("/events")
    assert not any(item["id"] == conv_id for item in r2_list.json()["items"])
    r2_direct = client.get(f"/events/{conv_id}")
    assert r2_direct.status_code == 403

    # Step 3: Turn back ON
    client.put("/permissions", json={"category": "conversation", "is_enabled": True})

    # Now accessible again
    r3_list = client.get("/events")
    assert any(item["id"] == conv_id for item in r3_list.json()["items"])
    r3_direct = client.get(f"/events/{conv_id}")
    assert r3_direct.status_code == 200
