from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import CrowdMetric, Event, Incident, OperatorAction
from conftest import client


def receive_type(ws, expected, maximum=4):
    for _ in range(maximum):
        message = ws.receive_json()
        if message["type"] == expected:
            return message
    raise AssertionError(f"Did not receive {expected}")


def test_member2_contract_event_to_lifecycle_and_realtime_updates():
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_E2E_001",
        "camera_id": "CAM_PLATFORM_01",
        "timestamp": 1787218200000,
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
        "track_ids": ["17", "22"],
        "zone_id": "ZONE_PLATFORM_EDGE",
        "persistence_ms": 2200,
        "people_count": 1,
        "metadata": {},
        "evidence": {
            "snapshot_path": None,
            "clip_path": None
        }
    }

    with client.websocket_connect("/ws/events") as ws:
        assert ws.receive_json()["type"] == "connection-established"
        accepted = client.post("/api/events", json=event)
        assert accepted.status_code == 200
        assert receive_type(ws, "event.created")["data"]["event_id"] == event["event_id"]
        assert receive_type(ws, "crowd.updated")["data"]["people_count"] == 1

        verify = client.post(f"/api/incidents/{event['event_id']}/verify", json={"user": "operator_01"})
        assert verify.status_code == 200
        assert receive_type(ws, "incident.updated")["data"]["status"] == "VERIFIED"

        assign = client.post(f"/api/incidents/{event['event_id']}/assign", json={
            "assigned_to": "RPF_TEAM_1", "user": "operator_01"
        })
        assert assign.status_code == 200
        assert receive_type(ws, "incident.updated")["data"]["status"] == "ASSIGNED"

        resolve = client.post(f"/api/incidents/{event['event_id']}/resolve", json={"user": "operator_01"})
        assert resolve.status_code == 200
        assert receive_type(ws, "incident.updated")["data"]["status"] == "RESOLVED"

    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Event)) == 1
        assert db.scalar(select(func.count()).select_from(CrowdMetric)) == 1
        incident = db.scalar(select(Incident).where(Incident.event_id == event["event_id"]))
        assert incident.status == "RESOLVED"
        assert db.scalar(select(func.count()).select_from(OperatorAction)) == 3