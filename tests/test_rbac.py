def test_rbac_admin_endpoint_forbidden_for_asha(client):
    asha_token = client.post("/auth/login", json={"user_id": "asha", "password": "asha123"}).json()["access_token"]
    
    # ASHA worker attempts to access admin dashboard
    res = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {asha_token}"})
    assert res.status_code == 403

def test_rbac_admin_endpoint_allowed_for_admin(client):
    admin_token = client.post("/auth/login", json={"user_id": "admin", "password": "admin123"}).json()["access_token"]
    
    res = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert "total_screenings" in res.json()
