# SIH1349 Backend API Contract Version 1.0

## Contract Version
**event-v1** — Canonical shared event contract between Member 2, Member 3, Member 4, and Member 5 integration.

The repository-level contract is authoritative: `docs/contracts/event-v1.schema.json`.

Backend documentation explains transport/API behavior but does not redefine incompatible event fields.

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

**Description:** Accept and process an AI-generated event validated against the canonical event-v1 schema.

**Request (canonical event-v1 shape):**
```json
{
  "schema_version": "event-v1",
  "event_id": "EVT_000123",
  "camera_id": "CAM_PLATFORM_01",
  "timestamp": 1787218200000,
  "event_type": "restricted_zone_intrusion",
  "severity": "HIGH",
  "confidence": 0.92,
  "track_ids": ["17"],
  "zone_id": "ZONE_PLATFORM_EDGE",
  "persistence_ms": 2200,
  "people_count": 1,
  "evidence": {"snapshot_path": null, "clip_path": null},
  "metadata": {}
}
```

**Field details:**

| Field | Required | Description |
|-------|----------|-------------|
| `schema_version` | Yes | Must be `"event-v1"` |
| `event_id` | Yes | Unique event identifier |
| `camera_id` | Yes | Camera identifier |
| `timestamp` | Yes | **Integer Unix epoch milliseconds UTC** (e.g. `1787218200000`). **Do not send ISO-8601 strings.** |
| `event_type` | Yes | Type of event, e.g. `restricted_zone_intrusion` |
| `severity` | Yes | Severity level. **Uppercase only**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `confidence` | Yes | Confidence score. **Must be 0.0–1.0** |
| `track_ids` | Optional | Array of track identifiers associated with the event |
| `zone_id` | Optional | Zone/Track identifier per event type |
| `persistence_ms` | Optional | Persistence duration in milliseconds. **Integer >= 0** |
| `people_count` | Optional | Number of people detected. **Integer >= 0** |
| `evidence` | Optional | Snapshot and clip path references |
| `metadata` | Optional | Additional structured AI metadata (JSON object) |

**Validation rules:**
- `schema_version` must be `"event-v1"` (any other value, e.g. `"1.0"`, is rejected)
- `timestamp` must be an **integer** representing Unix epoch milliseconds UTC
- `confidence` must be 0.0–1.0 (enforced by `ge=0, le=1`)
- `severity` must be one of `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` (uppercase)
- `track_ids`, if provided, must be an array of strings
- `zone_id`, if provided, must be a string or null
- `persistence_ms`, if provided, must be an integer >= 0
- `people_count`, if provided, must be an integer >= 0
- `event_id` must be unique (duplicate returns HTTP 409)

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
    "code": "INVALID_SCHEMA_VERSION",
    "message": "schema_version must be event-v1"
  }
}
```

**or**

```json
{
  "ok": false,
  "error": {
    "code": "INVALID_TIMESTAMP",
    "message": "timestamp must be integer Unix epoch milliseconds"
  }
}
```

**or**

```json
{
  "ok": false,
  "error": {
    "code": "INVALID_CONFIDENCE",
    "message": "confidence must be 0.0–1.0"
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

**Query parameters:**
| Parameter | Description |
|-----------|-------------|
| `camera_id` | Filter by camera ID |
| `event_type` | Filter by event type |
| `severity` | Filter by severity level |
| `start_time` | Filter events from this timestamp. **ISO-8601 query parameter** (e.g. `2026-08-20T00:00:00+05:30`). *Documented separately from event payload timestamp.* |
| `end_time` | Filter events until this timestamp. **ISO-8601 query parameter**. |
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
      "people_count": 63,
      "track_ids": ["17"],
      "persistence_ms": 2200
    }
  ]
}
```

**Note:** The `timestamp` in the GET response is the **database internal representation** (ISO-8601 datetime), *separate from* the canonical event payload timestamp (Unix epoch milliseconds). Query filters `start_time`/`end_time` use ISO-8601 strings.

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

**Description:** Transition VERIFIED → ASSIGNED.

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
NEW → VERIFIED → ASSIGNED → RESOLVED
         ↓              ↓
       DISMISSED
```

**Invalid transitions:**
- NEW → RESOLVED (must go through VERIFIED/ASSIGNED first)
- DISMISSED → ASSIGNED (invalid once dismissed)
- RESOLVED → VERIFIED (cannot re-verify a resolved incident)

---

## 9. GET /api/crowd

**Description:** Return crowd metrics history.

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

**Payload (canonical event-v1 shape):**
```json
{
  "type": "event.created",
  "data": {
    "event_id": "EVT_000123",
    "camera_id": "CAM_PLATFORM_01",
    "event_type": "restricted_zone_intrusion",
    "severity": "HIGH",
    "confidence": 0.92,
    "timestamp": 1787218200000,  // Unix epoch milliseconds
    "track_ids": ["17"],         // optional
    "zone_id": "ZONE_PLATFORM_EDGE",   // optional
    "persistence_ms": 2200,      // optional, integer >= 0
    "people_count": 1            // optional, integer >= 0
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
    "timestamp": 1787218200000  // Unix epoch milliseconds
  }
}
```

**Message type summary:**
| Type | Payload | When broadcast |
|------|---------|----------------|
| `connection-established` | `{type, data: {client_id}}` | WebSocket connection accepted |
| `event.created` | `{type, data: {event_id, camera_id, event_type, severity, confidence, timestamp, [track_ids], [zone_id], [persistence_ms], [people_count]}}` | New AI event accepted |
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
```

Successful responses use: `{"ok": true, "data": {...}}`

---

## Stability Guarantees (event-v1 Contract)

Following field names **must not** change without incrementing contract version:
- `event_id`, `camera_id`, `event_type`, `severity`, `confidence`, `schema_version`, `timestamp` (POST payload)
- `incident_id`, `event_id`, `status`, `assigned_to` (incident APIs)
- `camera_id`, `zone_id`, `people_count`, `timestamp` (GET /api/crowd) — timestamp is ISO-8601 datetime
- WebSocket message types: `connection-established`, `event.created`, `incident.updated`, `crowd.updated`
- WebSocket payload field names within each message type

Member 2 and Member 4 can rely on these field names being stable.

**Canonical shared schema is authoritative: `docs/contracts/event-v1.schema.json`**