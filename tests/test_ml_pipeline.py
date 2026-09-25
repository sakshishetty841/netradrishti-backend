import io
import pytest
from PIL import Image, ImageDraw
from app.ai.model_adapter import PyTorchRetinalModel, HeuristicRetinalModel, screening_model
from ml.explainability.gradcam import generate_gradcam_overlay
from ml.preprocessing.pipeline import preprocess_image_bytes

def test_model_loading():
    """Verify PyTorch model weights loading and fallback behavior"""
    model_adapter = PyTorchRetinalModel(model_path="ml/models/dr_model_best.pth")
    assert model_adapter.is_loaded == True
    assert model_adapter.model is not None

def test_missing_model_fallback():
    """Verify graceful fallback when model path does not exist"""
    model_adapter = PyTorchRetinalModel(model_path="ml/models/non_existent_model.pth")
    assert model_adapter.is_loaded == False

def test_pytorch_inference_and_probabilities(sample_fundus_image_bytes):
    """Verify 5-class DR prediction and probability scores output"""
    res = screening_model.predict(sample_fundus_image_bytes)
    assert "prediction" in res
    assert "grade" in res
    assert "confidence" in res
    assert "probabilities" in res
    
    probs = res["probabilities"]
    assert len(probs) == 5
    for i in range(5):
        assert str(i) in probs
        assert 0.0 <= probs[str(i)] <= 1.0
        
    prob_sum = sum(probs.values())
    assert abs(prob_sum - 1.0) < 0.01

def test_gradcam_overlay_generation(sample_fundus_image_bytes):
    """Verify PyTorch Grad-CAM heatmap generation"""
    if screening_model.is_loaded and screening_model.model is not None:
        tensor = preprocess_image_bytes(sample_fundus_image_bytes)
        explain_res = generate_gradcam_overlay(screening_model.model, tensor, sample_fundus_image_bytes, target_class=2)
        assert "heatmap_url" in explain_res
        assert explain_res["heatmap_url"].startswith("/media/heatmaps/")
        assert "explanation" in explain_res

def test_predict_endpoint_with_ml_model(client, sample_fundus_image_bytes):
    """Verify POST /predict legacy contract with trained ML model output"""
    login_res = client.post("/auth/login", json={"user_id": "asha", "password": "asha123"})
    token = login_res.json()["access_token"]
    
    files = {"image": ("test_fundus.jpg", sample_fundus_image_bytes, "image/jpeg")}
    data = {"eye": "RIGHT"}
    
    res = client.post(
        "/predict",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert res.status_code == 200
    json_data = res.json()
    
    # Legacy contract keys
    assert "grade" in json_data
    assert "confidence" in json_data
    assert "heatmap_url" in json_data
    assert "explanation" in json_data
    assert "recommendation" in json_data
    assert "urgency" in json_data
    
    # Extended ML keys
    assert "risk_context" in json_data
    assert "probabilities" in json_data["risk_context"]

def test_poor_quality_image_gating(client, blurry_image_bytes):
    """Verify automated quality assessment halts AI prediction on poor images"""
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

def test_invalid_corrupted_file_upload(client):
    """Verify system rejects corrupted non-image byte uploads"""
    login_res = client.post("/auth/login", json={"user_id": "asha", "password": "asha123"})
    token = login_res.json()["access_token"]
    
    files = {"image": ("corrupted.jpg", b"NOT_AN_IMAGE_HEADER_BYTES", "image/jpeg")}
    
    res = client.post(
        "/predict",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert res.status_code == 200
    data = res.json()
    assert data["image_quality"] == "poor"
    assert "validation failed" in data["explanation"].lower()
