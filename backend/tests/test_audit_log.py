import pytest


def test_audit_entries_created_for_important_actions(client):
    """
    Requirements:
    - Audit entries are created for important actions:
      * Event creation
      * Event deletion
      * Permission updates
      * Blocked / Allowed direct accesses
    """
    # 1. Action: Create event
    res = client.post("/events", json={
        "type": "note",
        "title": "Audited Note",
        "content": "Check log generation"
    })
    event_id = res.json()["id"]

    # 2. Action: Update permission (turn OFF note)
    client.put("/permissions", json={
        "category": "note",
        "is_enabled": False
    })

    # 3. Action: Attempt to access disabled event (Denied)
    denied_res = client.get(f"/events/{event_id}")
    assert denied_res.status_code == 403

    # 4. Action: Turn back ON and delete event
    client.put("/permissions", json={"category": "note", "is_enabled": True})
    client.delete(f"/events/{event_id}")

    # 5. Fetch audit log
    audit_resp = client.get("/audit-log")
    assert audit_resp.status_code == 200
    log_data = audit_resp.json()
    assert "items" in log_data
    assert log_data["total"] >= 4

    actions = [item["action"] for item in log_data["items"]]
    results = [item["result"] for item in log_data["items"]]

    # Verify key actions are tracked
    assert "CREATE_EVENT" in actions
    assert "PERMISSION_SET_OFF" in actions
    assert "PERMISSION_SET_ON" in actions
    assert "GET_EVENT_DETAIL" in actions
    assert "DELETE_EVENT" in actions

    # Verify DENIED was audited
    assert "DENIED" in results

    # Verify schema of each log item
    first_item = log_data["items"][0]
    for required_key in ["id", "timestamp", "user_id", "action", "event_type", "result"]:
        assert required_key in first_item


def test_audit_log_is_read_only(client):
    """
    Requirements:
    "The audit log should be read-only."
    Verify no modifying endpoints (POST, PUT, DELETE) exist on /audit-log.
    """
    post_resp = client.post("/audit-log", json={"action": "MALICIOUS_LOG"})
    assert post_resp.status_code in (405, 404)

    delete_resp = client.delete("/audit-log")
    assert delete_resp.status_code in (405, 404)

    put_resp = client.put("/audit-log", json={"action": "TAMPER"})
    assert put_resp.status_code in (405, 404)
