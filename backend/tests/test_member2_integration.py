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
        "schema_version": "1.0",
        "event_id": "EVT_MEMBER2_STYLE",
        "camera_id": "CAM_04",
        "timestamp": "2026-08-20T12:00:00+05:30",
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.94,
        "zone_id": "TRACK_ZONE",
        "people_count": 31,
        "metadata": {"producer": "member2", "correlation_key": "track-42"},
        "evidence": {"snapshot_path": "/evidence/frame.jpg", "clip_path": "/evidence/clip.mp4"},
    }

    with client.websocket_connect("/ws/events") as ws:
        assert ws.receive_json()["type"] == "connection-established"
        accepted = client.post("/api/events", json=event)
        assert accepted.status_code == 200
        assert receive_type(ws, "event.created")["data"]["event_id"] == event["event_id"]
        assert receive_type(ws, "crowd.updated")["data"]["people_count"] == 31

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
