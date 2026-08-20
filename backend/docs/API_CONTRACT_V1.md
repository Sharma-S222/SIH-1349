# SIH1349 Backend API Contract Version 1.0

## Contract Version
**1.0** — Frozen for Member 4 integration. Do not change field names or payload structures without incrementing contract version.

## Base URL
`http://localhost:8000`

---

## 1. GET /health

**Description:** Backend readiness check.

**Request:** `GET /health`

**Response (200):**
```json
{
  "ok": true,
  "data": {"status": "ready"}
}
```

**Error:** N/A (always returns 200)

---

## 2. POST /api/events

**Description:** Accept and process an AI-generated event. If the event type is a safety event, an Incident is automatically created with status NEW. If people_count is provided, a CrowdMetric is stored.

**Request:**
```json
{
  "schema_version": "1.0",
  "event_id": "EVT_000123",
  "camera_id": "CAM_04",
  "timestamp": "2026-08-20T09:00:00+05:30",
  "event_type": "restricted_zone_intrusion",
  "severity": "HIGH",
  "confidence": 0.92,
  "zone_id": "TRACK_ZONE",
  "people_count": 63,
  "metadata": {},
  "evidence": {
    "snapshot_path": null,
    "clip_path": null
  }
}
```

**Field descriptions:**
| Field | Required | Description |
|-------|----------|-------------|
| `schema_version` | Yes | Schema version, e.g. `"1.0"` |
| `event_id` | Yes | Unique event identifier, e.g. `"EVT_000123"` |
| `camera_id` | Yes | Camera identifier, e.g. `"CAM_04"` |
| `timestamp` | Yes | ISO-8601 formatted timestamp |
| `event_type` | Yes | Type of event, e.g. `"restricted_zone_intrusion"` |
| `severity` | Yes | Severity level. Allowed values: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `confidence` | Yes | Confidence score. Must be 0.0–1.0 |
| `zone_id` | Optional | Zone/Track identifier per event type |
| `people_count` | Optional | Number of people detected |
| `metadata` | Optional | Additional structured AI metadata (JSON object) |
| `evidence` | Optional | Snapshot and clip path references |

**Allowed severity values:** `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` (as defined in the Pydantic AIEvent schema)

**Validation rules:**
- `confidence` must be 0–1 (enforced by `ge=0, le=1` in schema)
- `timestamp` must be valid ISO-8601 (enforced by `@field_validator`)
- `event_id` must be unique (duplicate returns HTTP 409)
- `camera_id` required (enforced by Pydantic schema)

**Duplicate behavior:**
- Same `event_id` sent twice → HTTP 409 conflict
- Not inserted again
- Not broadcast again

**Response (200 success):**
```json
{
  "ok": true,
  "data": {"event_id": "EVT_000123"}
}
```

**Response (validation error):**
```json
{
  "ok": false,
  "error": {
    "code": "INVALID_TIMESTAMP",
    "message": "timestamp must be ISO-8601 format"
  }
}
```

**Response (duplicate event):**
```json
{
  "ok": false,
  "error": {
    "code": "DUPLICATE_EVENT",
    "message": "event_id 'EVT_000123' already accepted"
  }
}
```

**Side effects:**
- If `event_type` is a safety event type, an `Incident` is automatically created with status `NEW`
- If `people_count` is provided, a `CrowdMetric` is stored (new row per observation, preserving time-series history)
- Broadcasts `event.created` via WebSocket to all connected clients
- Broadcasts `crowd.updated` if `people_count` exists

**Safety event types:** `restricted_zone_intrusion`, `fall_detected`, `abandoned_object`, `violence_detected`, `crowd_overload`, `fire_or_smoke`

---

## 3. GET /api/events

**Description:** Return event history with optional filtering.

**Request:** `GET /api/events?camera_id=CAM_04&event_type=restricted_zone_intrusion&severity=HIGH&start_time=2026-08-20T00:00:00+05:30&end_time=2026-08-20T23:59:59+05:30&limit=100`

**Query parameters:**
| Parameter | Description |
|-----------|-------------|
| `camera_id` | Filter by camera ID |
| `event_type` | Filter by event type |
| `severity` | Filter by severity level |
| `start_time` | Filter events from this timestamp (ISO-8601) |
| `end_time` | Filter events until this timestamp (ISO-8601) |
| `limit` | Maximum number of results (default: 100) |

**Representative request:**
```
GET /api/events?camera_id=CAM_04&severity=HIGH
```

**Response (200):**
```json
{
  "ok": true,
  "data": [
    {
      "event_id": "EVT_000123",
      "camera_id": "CAM_04",
      "event_type": "restricted_zone_intrusion",
      "severity": "HIGH",
      "confidence": 0.92,
      "timestamp": "2026-08-20T08:00:00+05:30",
      "zone_id": "TRACK_ZONE",
      "people_count": 63
    }
  ]
}
```

**Error:** N/A (always returns 200, possibly with empty `data` array)

---

## 4. GET /api/incidents

**Description:** Return list of incidents.

**Request:** `GET /api/incidents`

**Response (200):**
```json
{
  "ok": true,
  "data": [
    {
      "incident_id": 1,
      "event_id": "EVT_000123",
      "status": "VERIFIED",
      "assigned_to": "RPF_TEAM_1",
      "created_at": "2026-08-20T08:00:00+05:30",
      "resolved_at": "2026-08-20T09:30:00+05:30"
    }
  ]
}
```

**Error:** N/A (always returns 200, possibly with empty `data` array)

---

## 5. POST /api/incidents/{id}/verify

**Description:** Transition incident from NEW → VERIFIED.

**Request:**
```json
{
  "user": "operator_01",
  "note": "Confirmed intrusion"
}
```

**Response (200):**
```json
{
  "ok": true,
  "data": {"status": "VERIFIED"}
}
```

**Response (409 invalid transition):**
```json
{
  "ok": false,
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "cannot transition from 'NEW' to 'RESOLVED'"
  }
}
```

**Request body field descriptions:**
- `user`: Operator identifier, e.g. `"operator_01"`
- `note`: Free-text note, e.g. `"Confirmed intrusion"`

---

## 6. POST /api/incidents/{id}/dismiss

**Description:** Transition incident → DISMISSED (false alert).

**Request:**
```json
{
  "user": "operator_01",
  "note": "False alarm"
}
```

**Response (200):**
```json
{
  "ok": true,
  "data": {"status": "DISMISSED"}
}
```

**Request body field descriptions:**
- `user`: Operator identifier
- `note`: Free-text note

---

## 7. POST /api/incidents/{id}/assign

**Description:** Transition VERIFIED → ASSIGNED. Assign to a response team.

**Request:**
```json
{
  "assigned_to": "RPF_TEAM_1",
  "user": "operator_01",
  "note": "Respond to Platform 2"
}
```

**Response (200):**
```json
{
  "ok": true,
  "data": {"status": "ASSIGNED", "assigned_to": "RPF_TEAM_1"}
}
```

**Request body field descriptions:**
- `assigned_to`: Team identifier, e.g. `"RPF_TEAM_1"`
- `user`: Operator identifier, e.g. `"operator_01"`
- `note`: Free-text note, e.g. `"Respond to Platform 2"`

---

## 8. POST /api/incidents/{id}/resolve

**Description:** Transition ASSIGNED → RESOLVED.

**Request:**
```json
{
  "user": "operator_01",
  "note": "Incident resolved"
}
```

**Response (200):**
```json
{
  "ok": true,
  "data": {"status": "RESOLVED", "resolved_at": "2026-08-20T09:30:00+05:30"}
}
```

**Response (409 invalid transition):** e.g. RESOLVED → VERIFIED is invalid.

**Request body field descriptions:**
- `user`: Operator identifier
- `note`: Free-text note

---

## Lifecycle Diagram

```
         ┌──→ DISMISSED
         │
NEW ─────┤
         │
         └──→ VERIFIED
                ↓
             ASSIGNED
                ↓
             RESOLVED
```

**Invalid transitions:**
- NEW → RESOLVED (must go through VERIFIED/ASSIGNED first)
- DISMISSED → ASSIGNED (invalid once dismissed)
- RESOLVED → VERIFIED (cannot re-verify a resolved incident)

---

## 9. GET /api/crowd

**Description:** Return crowd metrics history.

**Request:** `GET /api/crowd?camera_id=CAM_04&zone_id=TRACK_ZONE&start_time=2026-08-20T00:00:00+05:30&end_time=2026-08-20T23:59:59+05:30&limit=100`

**Query parameters:**
| Parameter | Description |
|-----------|-------------|
| `camera_id` | Filter by camera ID |
| `zone_id` | Filter by zone ID |
| `start_time` | Filter from this timestamp (ISO-8601) |
| `end_time` | Filter until this timestamp (ISO-8601) |
| `limit` | Maximum results (default: 100) |

**Data ordering:** Newest-first (most recent first)

**Representative request:**
```
GET /api/crowd?camera_id=CAM_04&limit=50
```

**Response (200):**
```json
{
  "ok": true,
  "data": [
    {
      "camera_id": "CAM_04",
      "zone_id": "TRACK_ZONE",
      "people_count": 63,
      "timestamp": "2026-08-20T09:00:00+05:30"
    }
  ]
}
```

**Important:** Each event with `people_count` creates a new timestamped CrowdMetric row. History is preserved (not overwritten).

---

## WebSocket Endpoint

**URL:** `ws://localhost:8000/ws/events`

---

## 10. WebSocket Message Types

### `connection-established`

Sent when a client successfully connects.

**Payload:**
```json
{
  "type": "connection-established",
  "data": {"client_id": "<unique-id>"}
}
```

### `event.created`

Sent when a new AI event is accepted and persisted.

**Payload:**
```json
{
  "type": "event.created",
  "data": {
    "event_id": "EVT_000123",
    "camera_id": "CAM_04",
    "event_type": "restricted_zone_intrusion",
    "severity": "HIGH",
    "confidence": 0.92,
    "timestamp": "2026-08-20T09:00:00+05:30"
  }
}
```

### `incident.updated`

Sent when an incident state changes (verify/dismiss/assign/resolve).

**Payload:**
```json
{
  "type": "incident.updated",
  "data": {
    "incident_id": 12,
    "status": "ASSIGNED",
    "assigned_to": "RPF_TEAM_1"
  }
}
```

### `crowd.updated`

Sent when a new crowd metric is stored (event has `people_count`).

**Payload:**
```json
{
  "type": "crowd.updated",
  "data": {
    "camera_id": "CAM_04",
    "zone_id": "TRACK_ZONE",
    "people_count": 63,
    "timestamp": "2026-08-20T09:00:00+05:30"
  }
}
```

**Message type summary:**
| Type | Payload | When broadcast |
|------|---------|----------------|
| `connection-established` | `{type, data: {client_id}}` | WebSocket connection accepted |
| `event.created` | `{type, data: {event_id, camera_id, event_type, severity, confidence, timestamp}}` | New AI event accepted |
| `incident.updated` | `{type, data: {incident_id, status, assigned_to}}` | Incident state changes |
| `crowd.updated` | `{type, data: {camera_id, zone_id, people_count, timestamp}}` | Event with `people_count` stored |

---

## CORS Configuration

**Expected origins (from `.env` / `settings.cors_origins`):**
```
http://localhost:3000
http://localhost:5173
```

**Configuration:** `app/main.py` loads these from `app.config.Settings.cors_origins` and applies via `FastAPI CORSMiddleware`.

**Do NOT use:** `allow_origins=["*"]` for intended deployment.

---

## Error Response Format

All API errors follow this format:
```json
{
  "ok": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description"
  }
}
```

Successful responses use: `{"ok": true, "data": {...}}`

---

## Stability Guarantees (Contract Version 1.0)

Following field names **must not** change without incrementing contract version:
- `event_id`, `camera_id`, `event_type`, `severity`, `confidence`, `timestamp` (POST /api/events)
- `incident_id`, `event_id`, `status`, `assigned_to` (incident APIs)
- `camera_id`, `zone_id`, `people_count`, `timestamp` (GET /api/crowd)
- WebSocket message types: `connection-established`, `event.created`, `incident.updated`, `crowd.updated`
- WebSocket payload field names within each message type

Member 2 and Member 4 can rely on these field names being stable.
