def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_login_success(client):
    res = client.post("/auth/login", json={"user_id": "admin", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure(client):
    res = client.post("/auth/login", json={"user_id": "admin", "password": "wrongpassword"})
    assert res.status_code == 401

def test_get_me(client):
    login_res = client.post("/auth/login", json={"user_id": "asha", "password": "asha123"})
    token = login_res.json()["access_token"]
    
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["user_id"] == "asha"
    assert res.json()["role"] == "ASHA"
