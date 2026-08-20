#!/usr/bin/env python
"""Send representative Member 2 Contract V1 events to a running backend."""

import argparse
import json

try:
    from .member2_backend_client import BackendEventClient, generate_event_id, utc_timestamp
except ImportError:  # Direct script execution from the integration directory.
    from member2_backend_client import BackendEventClient, generate_event_id, utc_timestamp


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
        "schema_version": "1.0",
        "event_id": generate_event_id(),
        "camera_id": "CAM_04",
        "timestamp": utc_timestamp(),
        "event_type": event_type,
        "severity": severity,
        "confidence": 0.93,
        "zone_id": "TRACK_ZONE",
        "metadata": {"producer": "member2-simulator", "scenario": scenario},
        "evidence": {"snapshot_path": None, "clip_path": None},
    }
    if people_count is not None:
        event["people_count"] = people_count
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
