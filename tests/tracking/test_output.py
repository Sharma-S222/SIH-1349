import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tracking"))

from tracking.events import SafetyEvent
from tracking.output import EventOutput


def _make_event(event_type="zone_entry", severity="INFO", track_id=1, frame_index=0, timestamp_ms=1000):
    return SafetyEvent(
        event_type=event_type,
        severity=severity,
        confidence=0.9,
        track_id=track_id,
        zone_id="ZONE_A",
        frame_index=frame_index,
        timestamp_ms=timestamp_ms,
        persistence_frames=1,
        movement={},
        zone_transition={},
    )


def test_event_v1_schema_version():
    output = EventOutput()
    event = _make_event()
    payload = output.build_event(event=event, camera_id="CAM_0", epoch_ms=1700000000000)
    assert payload["schema_version"] == "event-v1"


def test_event_v1_timestamp_is_epoch_ms():
    output = EventOutput()
    event = _make_event(timestamp_ms=4000)
    epoch_ms = 1700000000000
    payload = output.build_event(event=event, camera_id="CAM_0", epoch_ms=epoch_ms)
    assert payload["timestamp"] == epoch_ms
    assert payload["metadata"]["source_timestamp_ms"] == 4000


def test_event_v1_track_ids_is_list():
    output = EventOutput()
    event = _make_event(track_id=5)
    payload = output.build_event(event=event, camera_id="CAM_0", epoch_ms=1700000000000)
    assert isinstance(payload["track_ids"], list)
    assert payload["track_ids"] == ["5"]
    assert all(isinstance(tid, str) for tid in payload["track_ids"])


def test_event_v1_event_id_is_uuid():
    output = EventOutput()
    event = _make_event()
    payload = output.build_event(event=event, camera_id="CAM_0", epoch_ms=1700000000000)
    assert isinstance(payload["event_id"], str)
    uuid.UUID(payload["event_id"])


def test_event_v1_severity_uppercase():
    output = EventOutput()
    for sev in ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        event = _make_event(severity=sev)
        payload = output.build_event(event=event, camera_id="CAM_0", epoch_ms=1700000000000)
        assert payload["severity"] == sev


def test_event_v1_camera_id():
    output = EventOutput()
    event = _make_event()
    payload = output.build_event(event=event, camera_id="CAM_0", epoch_ms=1700000000000)
    assert payload["camera_id"] == "CAM_0"


def test_event_v1_has_required_fields():
    output = EventOutput()
    event = _make_event()
    payload = output.build_event(event=event, camera_id="CAM_0", epoch_ms=1700000000000)
    required_fields = [
        "schema_version", "event_id", "camera_id", "frame_index",
        "timestamp", "event_type", "severity", "confidence",
        "track_ids", "zone_id", "persistence_ms",
        "movement", "zone_transition", "metadata",
    ]
    for field in required_fields:
        assert field in payload, f"Missing field: {field}"

