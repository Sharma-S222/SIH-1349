# Member 2 AI Integration — event-v1 Contract

Member 2 sends completed logical safety/crowd events to `POST http://localhost:8000/api/events`.
Member 1 and Member 2 AI code stays outside the backend; HTTP JSON is the architectural boundary.

The repository-level contract is authoritative:
`docs/contracts/event-v1.schema.json`

Backend documentation explains transport/API behavior but does not redefine incompatible event fields.

## Canonical event-v1 payload

Member 2 should produce **ONE event object** that:

- **passes** validation against `docs/contracts/event-v1.schema.json`
- **and** is directly accepted by `POST /api/events`

No backend-specific translation should be required.

### Example canonical event object

```json
{
  "schema_version": "event-v1",
  "event_id": "EVT_000123",
  "camera_id": "CAM_04",
  "timestamp": 1787218200000,
  "event_type": "restricted_zone_intrusion",
  "severity": "HIGH",
  "confidence": 0.92,
  "zone_id": "TRACK_ZONE",
  "people_count": 63,
  "track_ids": ["42"],
  "persistence_ms": 2200,
  "evidence": {"snapshot_path": null, "clip_path": null},
  "metadata": {"producer": "member2-simulator", "scenario": "intrusion"}
}
```

### Field definitions (canonical)

| Field | Required? | Description |
|-------|-----------|-------------|
| `schema_version` | Yes | Must be `"event-v1"` |
| `event_id` | Yes | Globally unique logical event ID. Use `EVT_<uuid>`, not restart-sensitive counters. |
| `camera_id` | Yes | Camera identifier agreed by the team. |
| `timestamp` | Yes | **Integer Unix epoch milliseconds UTC** (e.g. `1787218200000`). *Do not send ISO-8601 strings in the event payload.* |
| `event_type` | Yes | Centralized logical event name. See the "Central event-type mapping" table below. |
| `severity` | Yes | One of `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. Uppercase only. |
| `confidence` | Yes | Normalized value from `0.0` through `1.0` inclusive. |
| `track_ids` | Optional | Array of track identifiers associated with the event. |
| `zone_id` | Optional | Zone/Track identifier per event type. |
| `persistence_ms` | Optional | Persistence duration in milliseconds. Integer >= 0. |
| `people_count` | Optional | Non-negative count. When present, the backend appends a timestamped `CrowdMetric`. |
| `evidence` | Optional | Snapshot and clip path references only. No raw image/video bytes. |
| `metadata` | Optional | Additional structured JSON metadata. Do not move explicit contract fields here. |

**Important:** An event remains valid without `people_count`. Evidence paths on one laptop may not be accessible from another; during cross-laptop integration prefer an agreed shared/static URL or shared-storage reference.

### Central event-type mapping

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

### Severity should reflect team-agreed operating guidance

—for example informational crowd observations may be `LOW`/`MEDIUM`, confirmed safety risks may be `HIGH`, and immediate threats may be `CRITICAL`. The backend deliberately does not encode speculative railway policy.

### Persistent detections and alert storms

The backend rejects an exact repeated `event_id` with HTTP 409, but it cannot know that hundreds of new UUIDs describe the same person remaining in one zone. Member 2 should correlate detections and apply a controlled cooldown:

1. Recognize one logical incident from tracking/safety state.
2. Emit one event with one UUID.
3. Suppress equivalent alerts for the chosen cooldown while maintaining producer state.
4. Emit a new event only when the logical incident has ended and a genuinely new incident begins.

Do not move tracking into the backend.

### Python producer example (canonical format)

```python
from integration.member2_backend_client import (
    BackendEventClient,
    generate_event_id,
    utc_timestamp_epoch_ms,
)

client = BackendEventClient("http://localhost:8000", timeout=5.0)
event = {
    "schema_version": "event-v1",
    "event_id": generate_event_id(),
    "camera_id": "CAM_04",
    "timestamp": utc_timestamp_epoch_ms(),  # integer epoch milliseconds
    "event_type": "fall_detected",
    "severity": "CRITICAL",
    "confidence": 0.96,
    "zone_id": "PLATFORM_2",
    # optional canonical fields:
    "people_count": 1,
    "track_ids": ["track-42"],
    "persistence_ms": 5000,
    "evidence": {"snapshot_path": None, "clip_path": None},
    "metadata": {"producer": "member2-simulator", "scenario": "fall"},
}

result = client.send_event(event)
if not result.accepted:
    print(result.status_code, result.error)
    # Continue the AI processing loop; one backend failure is not fatal.
```

The reusable client distinguishes accepted, duplicate, validation/other HTTP rejection, serialization, and network outcomes. It performs at most one small controlled retry for network failures.

### Simulator

With the backend running:

```powershell
python integration/simulate_member2.py --scenario intrusion
python integration/simulate_member2.py --scenario fall
python integration/simulate_member2.py --scenario abandoned-object
python integration/simulate_member2.py --scenario crowd-overload
python integration/simulate_member2.py --scenario fire
```

Use `--backend-url http://<BACKEND_LAN_IP>:8000` for same-LAN integration; no IP is hard-coded.

---
*Note: This document was updated to align with the canonical event-v1 contract at docs/contracts/event-v1.schema.json. Previous versions used schema_version "1.0" and ISO-8601 timestamps; those formats are no longer accepted for POST /api/events."""