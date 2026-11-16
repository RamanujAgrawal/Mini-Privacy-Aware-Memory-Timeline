def test_root_serves_frontend(client):
    """Verify that root / serves index.html."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "CHRONIS" in response.text
    assert "Privacy Controls" in response.text
