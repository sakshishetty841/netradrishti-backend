def test_phc_doctor_review(client, sample_fundus_image_bytes):
    # 1. ASHA creates patient & legacy prediction
    asha_token = client.post("/auth/login", json={"user_id": "asha", "password": "asha123"}).json()["access_token"]
    files = {"image": ("case.jpg", sample_fundus_image_bytes, "image/jpeg")}
    pred_res = client.post("/predict", files=files, headers={"Authorization": f"Bearer {asha_token}"}).json()
    screening_id = pred_res["screening_id"]
    
    # 2. PHC Doctor reviews case
    doc_token = client.post("/auth/login", json={"user_id": "doctor", "password": "doctor123"}).json()["access_token"]
    review_res = client.post(
        f"/doctor/cases/{screening_id}/review",
        json={"decision": "AGREE_WITH_SCREENING", "notes": "Agreed with AI triage recommendation."},
        headers={"Authorization": f"Bearer {doc_token}"}
    )
    assert review_res.status_code == 200
    assert review_res.json()["decision"] == "AGREE_WITH_SCREENING"
