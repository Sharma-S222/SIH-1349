#!/usr/bin/env python
"""Deterministic HTTP smoke test for a running SIH1349 backend."""

import argparse
import json
import uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def request_json(base_url, path, method="GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-url", default="http://localhost:8000")
    args = parser.parse_args()
    event_id = f"EVT_SMOKE_{uuid.uuid4()}"
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    event = {
        "schema_version": "1.0",
        "event_id": event_id,
        "camera_id": "CAM_SMOKE",
        "timestamp": timestamp,
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.9,
        "zone_id": "TRACK_ZONE",
        "people_count": 7,
    }

    status, health = request_json(args.backend_url, "/health")
    assert status == 200 and health["data"]["status"] == "ready"
    status, accepted = request_json(args.backend_url, "/api/events", "POST", event)
    assert status == 200 and accepted["data"]["event_id"] == event_id
    _, events = request_json(args.backend_url, f"/api/events?camera_id=CAM_SMOKE")
    assert any(item["event_id"] == event_id for item in events["data"])
    _, incidents = request_json(args.backend_url, "/api/incidents")
    assert any(item["event_id"] == event_id and item["status"] == "NEW" for item in incidents["data"])
    _, crowd = request_json(args.backend_url, "/api/crowd?camera_id=CAM_SMOKE")
    assert any(item["people_count"] == 7 for item in crowd["data"])
    print(f"Smoke test passed for {event_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
