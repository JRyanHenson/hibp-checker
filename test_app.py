from app import app

def test_health_check():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200

def test_home_page():
    client = app.test_client()
    response = client.get("/tools/hibp/")
    assert response.status_code == 200
    assert b"HIBP" in response.data
