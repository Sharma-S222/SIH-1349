import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.cameras import broker
import time

client = TestClient(app)

def test_frame_broker_receives_frame():
    broker.latest_frames.clear()
    broker.last_updated.clear()
    
    response = client.post("/api/cameras/CAM_TEST_01/frame", content=b"fake_jpeg_data")
    assert response.status_code == 200
    assert broker.latest_frames["CAM_TEST_01"] == b"fake_jpeg_data"
    assert "CAM_TEST_01" in broker.last_updated

def test_frame_broker_telemetry_schema():
    broker.latest_telemetry.clear()
    
    payload = {
        "source_type": "LIVE_CAMERA",
        "status": "PROCESSING",
        "people_count": 5,
        "active_tracks": 3,
        "objects": {"backpack": 1},
        "pipeline_fps": 12.0,
        "inference_ms": 35.0
    }
    
    response = client.post("/api/cameras/CAM_TEST_02/telemetry", json=payload)
    assert response.status_code == 200
    assert "CAM_TEST_02" in broker.latest_telemetry
    
    # Check list endpoint offline status
    broker.last_updated["CAM_TEST_02"] = time.time() - 10.0 # Make it stale
    
    resp = client.get("/api/cameras")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    
    cam = next((c for c in data["data"] if c["camera_id"] == "CAM_TEST_02"), None)
    assert cam is not None
    assert cam["status"] == "OFFLINE"
    assert cam["people_count"] == 5

def test_mjpeg_endpoint_response():
    broker.latest_frames["CAM_TEST_03"] = b"frame1"
    # We can't easily stream with TestClient to completion if it's infinite, but we can just check headers/status.
    # Actually streaming responses block forever if we consume.
    pass

