def test_quality_check_rejection(client, blurry_image_bytes):
    login_res = client.post("/auth/login", json={"user_id": "asha", "password": "asha123"})
    token = login_res.json()["access_token"]
    
    files = {"image": ("blurry.jpg", blurry_image_bytes, "image/jpeg")}
    
    res = client.post(
        "/predict",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert res.status_code == 200
    data = res.json()
    assert data["image_quality"] == "poor"
    assert data["grade"] == "Poor Quality"
    assert "Rescan required" in data["recommendation"]
