#!/usr/bin/env python
"""Send representative Member 2 Contract V1 events to a running backend.

Events emitted here are designed to be accepted directly by POST /api/events
without any backend-specific translation. They conform to the canonical
event-v1 schema at docs/contracts/event-v1.schema.json.

SCENARIOS:
- intrusion:  restricted_zone_intrusion, HIGH, no people_count
- fall:     fall_detected, CRITICAL, no people_count
- abandoned-object:  abandoned_object, HIGH, no people_count
- crowd-overload:  crowd_overload, HIGH, 75 people
- fire:       fire_or_smoke, CRITICAL, no people_count

Each event uses:
  schema_version = "event-v1"
  timestamp = integer Unix epoch milliseconds UTC
  canonical fields as documented in API_CONTRACT_V1.md
"""
import argparse
import json
import time
import uuid

from .member2_backend_client import BackendEventClient, generate_event_id, utc_timestamp_epoch_ms


SCENARIOS = {
    "intrusion": ("restricted_zone_intrusion", "HIGH", None),
    "fall": ("fall_detected", "CRITICAL", None),
    "abandoned-object": ("abandoned_object", "HIGH", None),
    "crowd-overload": ("crowd_overload", "HIGH", 75),
    "fire": ("fire_or_smoke", "CRITICAL", None),
}


def build_event(scenario: str) -> dict:
    event_type, severity, people_count = SCENARIOS[scenario]
    event = {
        "schema_version": "event-v1",
        "event_id": generate_event_id(),
        "camera_id": "CAM_04",
        "timestamp": utc_timestamp_epoch_ms(),
        "event_type": event_type,
        "severity": severity,
        "confidence": 0.93,
        "zone_id": "TRACK_ZONE",
        "metadata": {"producer": "member2-simulator", "scenario": scenario},
        "evidence": {"snapshot_path": None, "clip_path": None},
    }
    if people_count is not None:
        event["people_count"] = people_count
    # Optional canonical fields (included when relevant)
    # track_ids and persistence_ms are optional; omitted here by default
    # people_count is included when the scenario has a value
    return event


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), required=True)
    parser.add_argument("--backend-url", default="http://localhost:8000")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    event = build_event(args.scenario)
    client = BackendEventClient(args.backend_url, timeout=args.timeout)
    result = client.send_event(event)

    print(f"generated event_id: {event['event_id']}")
    print(f"endpoint used: {client.endpoint}")
    print(f"HTTP status: {result.status_code if result.status_code is not None else 'unavailable'}")
    print(f"backend response: {json.dumps(result.response, indent=2) if result.response else result.error}")
    print(f"state: {'accepted' if result.accepted else 'rejected'}")
    return 0 if result.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())