"""
SIH1349 - Railway CCTV Intelligence System - Backend
Test incidents module with Contract V1 WebSocket and error format tests.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ─── Health ──────────────────────────────────────────────────────────


def test_health():
    """GET /health returns ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "data": {"status": "ready"}}


# ─── Event Contract V1 Tests ─────────────────────────────────────────


def test_valid_event():
    """Valid event POST returns 200 with ok=True."""
    import time
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_VALID_001",
        "camera_id": "CAM_01",
        "timestamp": int(time.time() * 1000),
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
    }
    resp = client.post("/api/events", json=event)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


def test_valid_event_z_timestamp():
    """Valid event with epoch-ms timestamp returns 200."""
    import time
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_VALID_Z_001",
        "camera_id": "CAM_01",
        "timestamp": int(time.time() * 1000),
        "event_type": "fall_detected",
        "severity": "MEDIUM",
        "confidence": 0.80,
    }
    resp = client.post("/api/events", json=event)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_invalid_event_missing_camera_id():
    """Event without camera_id returns 422."""
    event = {
        "schema_version": "1.0",
        "event_id": "EVT_NOCAM_001",
        "timestamp": "2026-08-19T21:15:22+05:30",
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
    }
    resp = client.post("/api/events", json=event)
    assert resp.status_code == 422


def test_invalid_confidence():
    """Event with confidence > 1 returns 422 (Pydantic ge/le validation)."""
    event = {
        "schema_version": "1.0",
        "event_id": "EVT_BAD_CONF_001",
        "camera_id": "CAM_01",
        "timestamp": "2026-08-19T21:15:22+05:30",
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 1.5,
    }
    resp = client.post("/api/events", json=event)
    assert resp.status_code == 422


def test_duplicate_event():
    """Duplicate event_id returns 409 with Contract V1 error format."""
    import time
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_DUP_001",
        "camera_id": "CAM_01",
        "timestamp": int(time.time() * 1000),
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
    }
    response1 = client.post("/api/events", json=event)
    assert response1.status_code == 200
    response2 = client.post("/api/events", json=event)
    assert response2.status_code == 409
    data = response2.json()
    assert data["ok"] is False
    assert "error" in data
    assert data["error"]["code"] == "DUPLICATE_EVENT"


def test_duplicate_event_no_double_send():
    """Second duplicate event also returns 409."""
    import time
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_DUP_BROADCAST_001",
        "camera_id": "CAM_04",
        "timestamp": int(time.time() * 1000),
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
    }
    response1 = client.post("/api/events", json=event)
    assert response1.status_code == 200
    response2 = client.post("/api/events", json=event)
    assert response2.status_code == 409


# ─── Incident Lifecycle Contract V1 Tests ────────────────────────────


def test_incident_creation():
    """Safety event auto-creates incident with status NEW.
    
    Uses GET /api/incidents (list) since the contract does not define
    GET /api/incidents/{id}.
    """
    import time
    event_id = "EVT_INC_001"
    event = {
        "schema_version": "event-v1",
        "event_id": event_id,
        "camera_id": "CAM_01",
        "timestamp": int(time.time() * 1000),
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
        "people_count": 10,
    }
    resp = client.post("/api/events", json=event)
    assert resp.status_code == 200

    # Locate the incident by filtering the list
    list_resp = client.get("/api/incidents")
    assert list_resp.status_code == 200
    incidents = list_resp.json()["data"]
    matching = [i for i in incidents if i["event_id"] == event_id]
    assert len(matching) == 1, f"Expected 1 incident for {event_id}, got {len(matching)}"
    assert matching[0]["status"] == "NEW"


def test_verify_incident():
    """Verify incident: NEW -> VERIFIED."""
    import time
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_VERIFY_001",
        "camera_id": "CAM_01",
        "timestamp": int(time.time() * 1000),
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
    }
    client.post("/api/events", json=event)
    resp = client.post("/api/incidents/EVT_VERIFY_001/verify", json={
        "user": "operator_01", "note": "Confirmed"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["status"] == "VERIFIED"


def test_dismiss_incident():
    """Dismiss incident: NEW -> DISMISSED."""
    import time
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_DISMISS_001",
        "camera_id": "CAM_01",
        "timestamp": int(time.time() * 1000),
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
    }
    client.post("/api/events", json=event)
    resp = client.post("/api/incidents/EVT_DISMISS_001/dismiss", json={
        "user": "operator_01", "note": "False alarm"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["status"] == "DISMISSED"


def test_assign_incident():
    """Assign incident: VERIFIED -> ASSIGNED."""
    import time
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_ASSIGN_001",
        "camera_id": "CAM_01",
        "timestamp": int(time.time() * 1000),
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
    }
    client.post("/api/events", json=event)
    # Verify first
    client.post("/api/incidents/EVT_ASSIGN_001/verify", json={
        "user": "operator_01", "note": "Confirmed"
    })
    # Then assign
    resp = client.post("/api/incidents/EVT_ASSIGN_001/assign", json={
        "assigned_to": "RPF_TEAM_1",
        "user": "operator_01",
        "note": "Respond"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["status"] == "ASSIGNED"
    assert data["data"]["assigned_to"] == "RPF_TEAM_1"


def test_resolve_incident():
    """Resolve incident: ASSIGNED -> RESOLVED."""
    import time
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_RESOLVE_001",
        "camera_id": "CAM_01",
        "timestamp": int(time.time() * 1000),
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
    }
    client.post("/api/events", json=event)
    # Verify
    client.post("/api/incidents/EVT_RESOLVE_001/verify", json={
        "user": "operator_01", "note": "Confirmed"
    })
    # Assign
    client.post("/api/incidents/EVT_RESOLVE_001/assign", json={
        "assigned_to": "RPF_TEAM_1",
        "user": "operator_01",
        "note": "Respond"
    })
    # Resolve
    resp = client.post("/api/incidents/EVT_RESOLVE_001/resolve", json={
        "user": "operator_01", "note": "Resolved"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["status"] == "RESOLVED"


def test_illegal_transition():
    """Illegal transition from DISMISSED to ASSIGNED returns 409 Conflict.
    
    Contract V1 (API_CONTRACT_V1.md) specifies 409 for invalid transitions.
    """
    import time
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_ILLEGAL_001",
        "camera_id": "CAM_01",
        "timestamp": int(time.time() * 1000),
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
    }
    client.post("/api/events", json=event)
    # Dismiss first
    client.post("/api/incidents/EVT_ILLEGAL_001/dismiss", json={
        "user": "operator_01", "note": "False alarm"
    })
    # Try illegal assign - should return 409 per Contract V1
    resp = client.post("/api/incidents/EVT_ILLEGAL_001/assign", json={
        "assigned_to": "RPF_TEAM_1",
        "user": "operator_01",
        "note": "Respond"
    })
    assert resp.status_code == 409
    data = resp.json()
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_TRANSITION"


# ─── WebSocket Contract V1 Tests ─────────────────────────────────────


def test_contract_ws_event_created():
    """WS /ws/events sends connection-established then event.created with Contract V1 keys."""
    import time
    with client.websocket_connect("/ws/events") as ws_a:
        # Receive connection-established message first (per Contract V1)
        connected = ws_a.receive_json()
        assert connected["type"] == "connection-established", \
            f"Expected connection-established, got {connected['type']}"
        assert "client_id" in connected["data"]

        # POST a new event
        event = {
            "schema_version": "event-v1",
            "event_id": "EVT_CONTRACT_WS_001",
            "camera_id": "CAM_02",
            "timestamp": int(time.time() * 1000),
            "event_type": "fall_detected",
            "severity": "MEDIUM",
            "confidence": 0.88,
        }
        client.post("/api/events", json=event)

        # Receive event.created message
        msg = ws_a.receive_json()
        assert msg["type"] == "event.created", f"Expected event.created, got {msg['type']}"

        # Verify data contains exactly Contract V1 keys
        expected_keys = {"event_id", "camera_id", "event_type", "severity", "confidence", "timestamp"}
        actual_keys = set(msg["data"].keys())
        assert actual_keys == expected_keys, \
            f"Expected keys {expected_keys}, got {actual_keys}"

        # Verify each field is present and non-null
        for key in expected_keys:
            assert key in msg["data"], f"Missing key: {key}"
            assert msg["data"][key] is not None, f"Null value for key: {key}"


def test_contract_ws_crowd_updated():
    """WS /ws/events sends crowd.updated when event has people_count."""
    import time
    with client.websocket_connect("/ws/events") as ws_a:
        # Consume connection-established
        connected = ws_a.receive_json()
        assert connected["type"] == "connection-established"

        # POST event with people_count
        event = {
            "schema_version": "event-v1",
            "event_id": "EVT_CONTRACT_CROWDWS_001",
            "camera_id": "CAM_01",
            "timestamp": int(time.time() * 1000),
            "event_type": "restricted_zone_intrusion",
            "severity": "HIGH",
            "confidence": 0.92,
            "people_count": 55,
        }
        client.post("/api/events", json=event)

        # Receive messages until crowd.updated is found (bounded to 5)
        crowd_message = None
        for _ in range(5):
            msg = ws_a.receive_json()
            if msg["type"] == "crowd.updated":
                crowd_message = msg
                break

        assert crowd_message is not None, "Did not receive crowd.updated via WebSocket"

        # Verify data contains Contract V1 keys
        expected_keys = {"camera_id", "zone_id", "people_count", "timestamp"}
        actual_keys = set(crowd_message["data"].keys())
        assert actual_keys == expected_keys, \
            f"Expected keys {expected_keys}, got {actual_keys}"

        # Verify field types
        assert isinstance(crowd_message["data"]["camera_id"], str)
        assert isinstance(crowd_message["data"]["zone_id"], str)
        assert isinstance(crowd_message["data"]["people_count"], int)
        assert isinstance(crowd_message["data"]["timestamp"], str)


def test_contract_ws_incident_updated():
    """WS /ws/events sends incident.updated through lifecycle."""
    import time
    with client.websocket_connect("/ws/events") as ws_a:
        # Receive connection-established message first
        connected = ws_a.receive_json()
        assert connected["type"] == "connection-established", \
            f"Expected connection-established, got {connected['type']}"

        # Create safety event
        event = {
            "schema_version": "event-v1",
            "event_id": "EVT_CONTRACT_INCWS_001",
            "camera_id": "CAM_01",
            "timestamp": int(time.time() * 1000),
            "event_type": "restricted_zone_intrusion",
            "severity": "HIGH",
            "confidence": 0.92,
            "people_count": 63,
        }
        client.post("/api/events", json=event)

        # Consume messages until event.created is found
        initial_msg = None
        for _ in range(5):
            msg = ws_a.receive_json()
            if msg["type"] == "event.created":
                initial_msg = msg
                break

        assert initial_msg is not None, "Did not receive event.created"

        # Perform NEW -> VERIFY
        resp = client.post("/api/incidents/EVT_CONTRACT_INCWS_001/verify", json={
            "user": "operator_01", "note": "Confirmed"
        })
        assert resp.status_code == 200

        # The event also has people_count, so crowd.updated is legitimately
        # queued after event.created. Consume until the lifecycle update.
        msg = None
        for _ in range(2):
            candidate = ws_a.receive_json()
            if candidate["type"] == "incident.updated":
                msg = candidate
                break

        assert msg is not None, "Did not receive incident.updated via WebSocket"

        # Verify data contains Contract V1 incident fields
        expected_keys = {"incident_id", "status", "assigned_to"}
        actual_keys = set(msg["data"].keys())
        assert actual_keys == expected_keys, \
            f"Expected keys {expected_keys}, got {actual_keys}"

        assert msg["data"]["status"] in ["NEW", "VERIFIED", "ASSIGNED", "RESOLVED", "DISMISSED"]

        # Now perform ASSIGN
        resp2 = client.post("/api/incidents/EVT_CONTRACT_INCWS_001/assign", json={
            "assigned_to": "RPF_TEAM_1",
            "user": "operator_01",
            "note": "Respond"
        })
        assert resp2.status_code == 200

        # Verify incident.updated again with ASSIGNED
        msg2 = ws_a.receive_json()
        assert msg2["type"] == "incident.updated"
        assert msg2["data"]["status"] == "ASSIGNED"
        assert msg2["data"]["assigned_to"] == "RPF_TEAM_1"

        # Then perform RESOLVE
        resp3 = client.post("/api/incidents/EVT_CONTRACT_INCWS_001/resolve", json={
            "user": "operator_01", "note": "Resolved"
        })
        assert resp3.status_code == 200

        # Verify incident.updated with RESOLVED
        msg3 = ws_a.receive_json()
        assert msg3["type"] == "incident.updated"
        assert msg3["data"]["status"] == "RESOLVED"


# ─── Error Contract V1 Test ──────────────────────────────────────────

def test_contract_error_format():
    """Application-level errors retain {ok: false, error: {code, message}} format."""
    import time
    # Trigger duplicate event (HTTP 409)
    event = {
        "schema_version": "event-v1",
        "event_id": "EVT_CONTRACT_ERROR_001",
        "camera_id": "CAM_01",
        "timestamp": int(time.time() * 1000),
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
    }
    resp1 = client.post("/api/events", json=event)
    assert resp1.status_code == 200

    resp2 = client.post("/api/events", json=event)
    assert resp2.status_code == 409
    data = resp2.json()

    # Contract V1 error format (NOT FastAPI's {"detail": ...} wrapper)
    assert "ok" in data, f"Error response should have 'ok' key, got {list(data.keys())}"
    assert data["ok"] is False, "Error ok should be False"
    assert "error" in data, f"Error response should have 'error' key, got {list(data.keys())}"
    assert "detail" not in data, f"Response must NOT use FastAPI 'detail' wrapper"
    assert "code" in data["error"], f"Error should have 'code', got {list(data['error'].keys())}"
    assert "message" in data["error"], f"Error should have 'message', got {list(data['error'].keys())}"
    assert isinstance(data["error"]["code"], str)
    assert isinstance(data["error"]["message"], str)


# ─── End Contract V1 Tests ────────────────────────────────────────────
