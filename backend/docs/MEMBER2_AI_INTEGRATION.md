# Member 2 AI Integration — Contract V1

Member 2 sends completed logical safety/crowd events to `POST http://localhost:8000/api/events`. Member 1 and Member 2 AI code stays outside the backend; HTTP JSON is the architectural boundary.

## Contract V1 payload

```json
{
  "schema_version": "1.0",
  "event_id": "EVT_550e8400-e29b-41d4-a716-446655440000",
  "camera_id": "CAM_04",
  "timestamp": "2026-08-20T12:00:00+05:30",
  "event_type": "restricted_zone_intrusion",
  "severity": "HIGH",
  "confidence": 0.92,
  "zone_id": "TRACK_ZONE",
  "people_count": 63,
  "metadata": {"track_id": "track-42"},
  "evidence": {
    "snapshot_path": "/shared/evidence/EVT_example.jpg",
    "clip_path": "/shared/evidence/EVT_example.mp4"
  }
}
```

- `schema_version`: frozen schema identifier, currently `1.0`.
- `event_id`: globally unique logical event ID. Use `EVT_<uuid>`, not restart-sensitive counters.
- `camera_id`: camera identifier agreed by the team.
- `timestamp`: timezone-aware ISO-8601 timestamp, either an offset such as `+05:30` or UTC `Z`.
- `event_type`: centralized logical event name; mappings are listed below.
- `severity`: one of `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
- `confidence`: normalized value from `0.0` through `1.0` inclusive.
- `zone_id`: optional zone/track reference.
- `people_count`: optional non-negative count. When present, the backend appends a timestamped `CrowdMetric`.
- `metadata`: optional reasonable-sized structured JSON metadata; do not place raw frames or video here.
- `evidence.snapshot_path` / `evidence.clip_path`: optional references only.

An event remains valid without `people_count`. Evidence paths on one laptop may not be accessible from another; during cross-laptop integration prefer an agreed shared/static URL or shared-storage reference. Cloud storage is outside the current phase.

## Python producer example

```python
from integration.member2_backend_client import (
    BackendEventClient,
    generate_event_id,
    utc_timestamp,
)

client = BackendEventClient("http://localhost:8000", timeout=5.0)
event = {
    "schema_version": "1.0",
    "event_id": generate_event_id(),
    "camera_id": "CAM_04",
    "timestamp": utc_timestamp(),
    "event_type": "fall_detected",
    "severity": "CRITICAL",
    "confidence": 0.96,
    "zone_id": "PLATFORM_2",
    "metadata": {"track_id": "track-42"},
    "evidence": {"snapshot_path": None, "clip_path": None},
}

result = client.send_event(event)
if not result.accepted:
    print(result.status_code, result.error)
    # Continue the AI processing loop; one backend failure is not fatal.
```

The reusable client distinguishes accepted, duplicate, validation/other HTTP rejection, serialization, and network outcomes. It performs at most one small controlled retry for network failures.

## Central event-type mapping

Do not rename these frozen safety types:

| Member 2 logical condition | Contract V1 `event_type` |
|---|---|
| Restricted polygon violation | `restricted_zone_intrusion` |
| Fall classifier positive | `fall_detected` |
| Unattended object threshold reached | `abandoned_object` |
| Violent behavior detected | `violence_detected` |
| Crowd threshold exceeded | `crowd_overload` |
| Fire/smoke detector positive | `fire_or_smoke` |

Member 2 decides when detections become a logical event. Member 3 validates and stores that event. Keep the mapping in one Member 2 module so different detectors do not invent spellings.

Severity should reflect team-agreed operating guidance—for example informational crowd observations may be `LOW`/`MEDIUM`, confirmed safety risks may be `HIGH`, and immediate threats may be `CRITICAL`. The backend deliberately does not encode speculative railway policy.

## Persistent detections and alert storms

The backend rejects an exact repeated `event_id` with HTTP 409, but it cannot know that hundreds of new UUIDs describe the same person remaining in one zone. Member 2 should correlate detections and apply a controlled cooldown:

1. Recognize one logical incident from tracking/safety state.
2. Emit one event with one UUID.
3. Suppress equivalent alerts for the chosen cooldown while maintaining producer state.
4. Emit a new event only when the logical incident has ended and a genuinely new incident begins.

Do not move tracking into the backend.

## Simulator

With the backend running:

```powershell
python integration/simulate_member2.py --scenario intrusion
python integration/simulate_member2.py --scenario fall
python integration/simulate_member2.py --scenario abandoned-object
python integration/simulate_member2.py --scenario crowd-overload
python integration/simulate_member2.py --scenario fire
```

Use `--backend-url http://<BACKEND_LAN_IP>:8000` for same-LAN integration; no IP is hard-coded.
