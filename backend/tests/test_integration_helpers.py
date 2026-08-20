from datetime import datetime

from integration.member2_backend_client import BackendEventClient, generate_event_id, utc_timestamp
from integration.simulate_member2 import SCENARIOS, build_event


def test_event_id_and_timestamp_helpers_are_contract_safe():
    first = generate_event_id()
    second = generate_event_id()
    assert first.startswith("EVT_")
    assert second.startswith("EVT_")
    assert first != second

    timestamp = utc_timestamp()
    assert timestamp.endswith("Z")
    assert datetime.fromisoformat(timestamp.replace("Z", "+00:00")).tzinfo is not None


def test_all_simulator_scenarios_build_contract_v1_events():
    for scenario in SCENARIOS:
        event = build_event(scenario)
        assert event["schema_version"] == "1.0"
        assert event["event_id"].startswith("EVT_")
        assert event["severity"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        assert 0 <= event["confidence"] <= 1


def test_client_network_failure_returns_result_instead_of_raising():
    client = BackendEventClient("http://127.0.0.1:9", timeout=0.1, retries=0)
    result = client.send_event(build_event("intrusion"))
    assert result.accepted is False
    assert result.status_code is None
    assert result.error.startswith("network failure:")
