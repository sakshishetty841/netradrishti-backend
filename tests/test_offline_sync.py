import uuid

def test_offline_sync_idempotency(client, sample_fundus_image_bytes):
    login_res = client.post("/auth/login", json={"user_id": "asha", "password": "asha123"})
    token = login_res.json()["access_token"]
    
    local_id = f"test-sync-{uuid.uuid4().hex}"
    
    files = {"image": ("sync_scan.jpg", sample_fundus_image_bytes, "image/jpeg")}
    data = {
        "local_id": local_id,
        "patient_name": "Ramesh Gowda",
        "age": "52",
        "gender": "Male",
        "village": "Rural Village",
        "eye": "LEFT"
    }
    
    # First sync call
    res1 = client.post(
        "/sync/screenings",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["status"] == "synced"
    assert d1["local_id"] == local_id
    
    # Second duplicate sync call with identical local_id
    files2 = {"image": ("sync_scan.jpg", sample_fundus_image_bytes, "image/jpeg")}
    res2 = client.post(
        "/sync/screenings",
        files=files2,
        data=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["status"] == "already_synced"
    assert d2["screening_id"] == d1["screening_id"]
