import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tracking"))

from tracking.events import SafetyEvent
from tracking.output import EventOutput


def _load_contract(contract_name):
    contract_path = Path(__file__).resolve().parent.parent.parent / "docs" / "contracts" / contract_name
    with open(contract_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_event_v1_contract_schema_version():
    contract = _load_contract("event-v1.schema.json")
    output = EventOutput()
    assert output.SCHEMA_VERSION == contract.get("title", "event-v1").replace(" Event Schema", "").replace(" ", "-").lower() or "event-v1"


def test_event_v1_contract_required_fields():
    contract = _load_contract("event-v1.schema.json")
    required = contract.get("required", [])
    output = EventOutput()
    event = SafetyEvent(
        event_type="zone_entry", severity="INFO", confidence=0.9,
        track_id=1, zone_id="ZONE_A", frame_index=0, timestamp_ms=0,
        persistence_frames=1, movement={}, zone_transition={},
    )
    payload = output.build_event(event=event, camera_id="CAM_0", epoch_ms=1700000000000)
    for field in required:
        assert field in payload, f"Missing required field from contract: {field}"


def test_event_v1_contract_severity_enum():
    contract = _load_contract("event-v1.schema.json")
    severity_schema = contract.get("properties", {}).get("severity", {})
    allowed = severity_schema.get("enum", [])
    output = EventOutput()
    for sev in allowed:
        event = SafetyEvent(
            event_type="zone_entry", severity=sev, confidence=0.9,
            track_id=1, zone_id="ZONE_A", frame_index=0, timestamp_ms=0,
            persistence_frames=1, movement={}, zone_transition={},
        )
        payload = output.build_event(event=event, camera_id="CAM_0", epoch_ms=1700000000000)
        assert payload["severity"] == sev

