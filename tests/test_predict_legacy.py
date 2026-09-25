def test_predict_legacy_endpoint(client, sample_fundus_image_bytes):
    # Login as ASHA
    login_res = client.post("/auth/login", json={"user_id": "asha", "password": "asha123"})
    token = login_res.json()["access_token"]
    
    files = {"image": ("test_retina.jpg", sample_fundus_image_bytes, "image/jpeg")}
    data = {"eye": "RIGHT"}
    
    res = client.post(
        "/predict",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert res.status_code == 200
    json_data = res.json()
    
    # Verify mandatory legacy keys expected by existing React frontend
    assert "grade" in json_data
    assert "confidence" in json_data
    assert "heatmap_url" in json_data
    assert "explanation" in json_data
    assert "recommendation" in json_data
    assert "urgency" in json_data
    
    # Verify values
    assert json_data["grade"] in ["No DR", "Mild", "Moderate", "Severe", "Proliferative"]
    assert 0.0 <= json_data["confidence"] <= 1.0
    assert isinstance(json_data["heatmap_url"], str)
