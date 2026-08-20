from pathlib import Path

from sqlalchemy import func, select

from app.database import SessionLocal
import app.api.events as events_module
from app.models import CrowdMetric, Event, Incident
from app.websocket.manager import manager
from conftest import client


def event_payload(event_id, camera_id="CAM_04", timestamp=1787218200000, **overrides):
    import time
    payload = {
        "schema_version": "event-v1",
        "event_id": event_id,
        "camera_id": camera_id,
        "timestamp": timestamp,  # integer Unix epoch milliseconds UTC
        "event_type": "passenger_flow",
        "severity": "LOW",
        "confidence": 0.85,
    }
    payload.update(overrides)
    return payload


def test_event_history_filters_by_camera():
    assert client.post("/api/events", json=event_payload("EVT_FILTER_1", "CAM_04")).status_code == 200
    assert client.post("/api/events", json=event_payload("EVT_FILTER_2", "CAM_09")).status_code == 200

    records = client.get("/api/events", params={"camera_id": "CAM_04"}).json()["data"]
    assert [record["event_id"] for record in records] == ["EVT_FILTER_1"]


def test_crowd_history_preserves_observations_filters_and_orders_newest_first():
    assert client.post("/api/events", json=event_payload(
        "EVT_CROWD_OLD", "CAM_04", 1787218200000, people_count=12
    )).status_code == 200
    assert client.post("/api/events", json=event_payload(
        "EVT_CROWD_NEW", "CAM_04", 1787218500000, people_count=18
    )).status_code == 200
    assert client.post("/api/events", json=event_payload(
        "EVT_CROWD_OTHER", "CAM_09", 1787218800000, people_count=30
    )).status_code == 200

    records = client.get("/api/crowd", params={"camera_id": "CAM_04"}).json()["data"]
    assert [record["people_count"] for record in records] == [18, 12]
    assert {record["camera_id"] for record in records} == {"CAM_04"}

    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(CrowdMetric)) == 3


def test_non_safety_people_count_creates_metric_without_incident():
    response = client.post("/api/events", json=event_payload(
        "EVT_NON_SAFETY_CROWD", people_count=22, event_type="passenger_flow"
    ))
    assert response.status_code == 200

    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(CrowdMetric)) == 1
        assert db.scalar(select(func.count()).select_from(Incident)) == 0


def test_multiple_websocket_clients_receive_event_created():
    with client.websocket_connect("/ws/events") as ws_a:
        with client.websocket_connect("/ws/events") as ws_b:
            assert ws_a.receive_json()["type"] == "connection-established"
            assert ws_b.receive_json()["type"] == "connection-established"
            response = client.post("/api/events", json=event_payload("EVT_MULTI_WS"))
            assert response.status_code == 200
            assert ws_a.receive_json()["type"] == "event.created"
            assert ws_b.receive_json()["type"] == "event.created"


def test_websocket_disconnect_isolated_from_remaining_client():
    with client.websocket_connect("/ws/events") as ws_b:
        assert ws_b.receive_json()["type"] == "connection-established"
        with client.websocket_connect("/ws/events") as ws_a:
            assert ws_a.receive_json()["type"] == "connection-established"
        response = client.post("/api/events", json=event_payload("EVT_AFTER_DISCONNECT"))
        assert response.status_code == 200
        message = ws_b.receive_json()
        assert message["type"] == "event.created"
        assert message["data"]["event_id"] == "EVT_AFTER_DISCONNECT"


def test_duplicate_has_no_duplicate_database_or_broadcast_effects(monkeypatch):
    broadcasts = []

    async def capture(message):
        broadcasts.append(message)

    monkeypatch.setattr(manager, "broadcast", capture)
    payload = event_payload(
        "EVT_DUP_EFFECTS",
        event_type="restricted_zone_intrusion",
        severity="HIGH",
        people_count=40,
    )
    assert client.post("/api/events", json=payload).status_code == 200
    # Simulate a process restart/other worker so only the database uniqueness
    # guarantee can reject the second request.
    events_module.accepted_event_ids.clear()
    duplicate = client.post("/api/events", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_EVENT"

    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Event)) == 1
        assert db.scalar(select(func.count()).select_from(Incident)) == 1
        assert db.scalar(select(func.count()).select_from(CrowdMetric)) == 1

    assert [message["type"] for message in broadcasts] == ["event.created", "crowd.updated"]


def test_backend_source_has_no_ai_runtime_dependencies():
    app_root = Path(__file__).parents[1] / "app"
    forbidden = ("cv2", "opencv", "ultralytics", "yolo", "torch", "tensorflow")
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in app_root.rglob("*.py"))
    for dependency in forbidden:
        assert f"import {dependency}" not in source
        assert f"from {dependency}" not in source


def test_query_limits_are_bounded():
    assert client.get("/api/events", params={"limit": 501}).status_code == 422
    assert client.get("/api/crowd", params={"limit": 0}).status_code == 422
    assert client.get("/api/incidents", params={"limit": 501}).status_code == 422


def test_validation_errors_use_contract_envelope_and_metadata_is_bounded():
    malformed = event_payload("EVT_BAD_CONFIDENCE", confidence=1.5)
    response = client.post("/api/events", json=malformed)
    assert response.status_code == 422
    assert response.json() == {
        "ok": False,
        "error": {"code": "VALIDATION_ERROR", "message": "request validation failed"},
    }

    oversized = event_payload("EVT_BIG_METADATA", metadata={"blob": "x" * 70_000})
    response = client.post("/api/events", json=oversized)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
