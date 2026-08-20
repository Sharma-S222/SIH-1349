# SIH1349 Member 4 — Frontend Integration Guide

## Backend URL
`http://localhost:8000`

**Ensure CORS is configured** with your frontend origin in `backend/.env`:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 1. Initial Data Load

When the dashboard opens, perform these REST calls in order:

```javascript
// 1. Health check
await fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(data => console.log('Backend OK:', data.ok))

// 2. Load current incidents
await fetch('http://localhost:8000/api/incidents')
  .then(r => r.json())
  .then(data => loadIncidents(data.data))

// 3. Load event history
await fetch('http://localhost:8000/api/events')
  .then(r => r.json())
  .then(data => loadEvents(data.data))

// 4. Load crowd history
await fetch('http://localhost:8000/api/crowd')
  .then(r => r.json())
  .then(data => loadCrowdHistory(data.data))
```

**Order matters:** REST provides historical state; WebSocket provides real-time changes after this point.

---

## 2. WebSocket Connection

Connect to the real-time event stream:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/events');
```

ws.onopen = () => {
  console.log('Connected to event stream');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleWebSocketMessage(message);
};

ws.onclose = () => {
  // Automatic reconnect after 2 seconds
  setTimeout(connectWebSocket, 2000);
};

ws.onerror = (err) => {
  console.error('WebSocket error:', err);
};

**Requirements:**
- Automatic reconnect on disconnect
- Avoid creating unlimited reconnect timers (use setTimeout with delay)
- Handle malformed messages safely (try/catch around JSON.parse)
- Do not crash UI when backend temporarily disconnects
```

---

## 3. WebSocket Message Handling

Handle each message type:

```javascript
function handleWebSocketMessage(message) {
  switch (message.type) {
    case 'connection-established':
      console.log('Connected client ID:', message.data.client_id);
      break;

    case 'event.created':
      // Add event alert/card
      handleEventCreated(message.data);
      break;

    case 'incident.updated':
      // Update incident status on sidebar
      handleIncidentUpdated(message.data);
      break;

    case 'crowd.updated':
      // Update crowd count display
      handleCrowdUpdated(message.data);
      break;

    default:
      // Unknown message type — ignore safely
      console.log('Unknown WebSocket message type:', message.type);
  }
}
```

---

## 4. event.created Handling (canonical event-v1 shape)

When a new event is created, the dashboard should destructure the canonical payload:

```javascript
function handleEventCreated(eventData) {
  const {
    event_id,
    camera_id,
    event_type,
    severity,
    confidence,
    timestamp,       // Unix epoch milliseconds (e.g. 1787218200000)
    track_ids,       // optional array of track IDs
    zone_id,         // optional zone identifier
    persistence_ms,  // optional persistence duration in ms
    people_count     // optional people count
  } = eventData;

  // Add event alert/card
  addEventAlert({
    id: event_id,
    camera: camera_id,
    type: event_type,
    severity: severity,
    confidence: confidence,
    time: timestamp,  // display as formatted date from epoch ms
  });

  // Highlight HIGH/CRITICAL severity appropriately
  if (severity === 'HIGH' || severity === 'CRITICAL') {
    highlightCriticalEvent(event_id);
  }

  // Optionally fetch full REST detail if needed
  // fetch(`http://localhost:8000/api/events/${event_id}`);

  // Track optional fields for display
  if (track_ids !== undefined) {
    console.log('Track IDs associated:', track_ids);
  }
  if (zone_id !== undefined) {
    console.log('Zone ID:', zone_id);
  }
  if (people_count !== undefined) {
    console.log('People count:', people_count);
  }
  if (persistence_ms !== undefined) {
    console.log('Persistence ms:', persistence_ms);
  }
}
```

**Key actions:**
- Add event alert/card to dashboard
- Display timestamp formatted from Unix epoch milliseconds
- Highlight HIGH/CRITICAL severity appropriately
- Optionally display track_ids, zone_id, persistence_ms, people_count

---

## 4. incident.updated Handling

When an incident state changes (verify/dismiss/assign/resolve):

```javascript
function handleIncidentUpdated(incidentData) {
  const { incident_id, status, assigned_to } = incidentData;

  // Update incident status on sidebar
  updateIncidentStatus(incident_id, status);

  // Update assigned team display
  if (assigned_to) {
    updateIncidentTeam(incident_id, assigned_to);
  }

  // Remove resolved incidents after a delay
  if (status === 'RESOLVED') {
    scheduleRemoveIncident(incident_id);
  }
}
```

**Key actions:**
- Update incident status on sidebar
- Update assigned team display
- Remove resolved incidents after a delay

---

## 5. crowd.updated Handling (canonical shape)

When crowd metrics update:

```javascript
function handleCrowdUpdated(crowdData) {
  const { camera_id, zone_id, people_count, timestamp } = crowdData;

  // Update crowd count display
  updateCrowdCount(camera_id, people_count);

  // Update timestamp display (format from Unix epoch ms)
  updateCrowdTimestamp(camera_id, timestamp);

  // Optionally update chart data
  // chartData[camera_id].push({ people_count, timestamp: new Date(timestamp) });
  // chart.redraw();
}
```

**Key actions:**
- Update crowd count display
- Update timestamp display (format from Unix epoch ms)
- Update chart data if chart is displayed

---

## 6. Incident Dashboard Workflow

### Alert Flow

1. Operator sees a NEW incident on the dashboard
2. Click **VERIFY** button:

```javascript
await fetch(`http://localhost:8000/api/incidents/${incident_id}/verify`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user: 'operator_01', note: 'Confirmed intrusion' })
})
```

3. Backend responds, broadcasts `incident.updated`
4. All connected clients receive the update automatically
5. Incident status changes to VERIFIED

### Then: ASSIGN

```javascript
await fetch(`http://localhost:8000/api/incidents/${incident_id}/assign`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    assigned_to: 'RPF_TEAM_1',
    user: 'operator_01',
    note: 'Respond to Platform 2'
  })
})
```

6. Backend broadcasts `incident.updated` with status ASSIGNED and assigned_to
7. All clients update their display

### Then: RESOLVE

```javascript
await fetch(`http://localhost:8000/api/incidents/${incident_id}/resolve`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user: 'operator_01', note: 'Incident resolved' })
})
```

8. Backend broadcasts `incident.updated` with status RESOLVED
9. Incident is removed from active list after delay

### False alert:

```javascript
await fetch(`http://localhost:8000/api/incidents/${incident_id}/dismiss`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user: 'operator_01', note: 'False alarm' })
})
```

10. Backend broadcasts `incident.updated` with status DISMISSED
11. Incident is removed from active list

---

## 6. CORS Preflight for WebSocket

The WebSocket endpoint `ws://localhost:8000/ws/events` does not require a preflight OPTIONS request. However, the REST API does:

```javascript
// Example: POST /api/events with CORS
await fetch('http://localhost:8000/api/events', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    // CORS headers are automatically handled by the browser
  },
  body: JSON.stringify(eventData)
})
```

If you get CORS errors, ensure your frontend origin is listed in the backend `.env`:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 7. Error Handling

All API responses follow this format:

**Success:**
```json
{ "ok": true, "data": {...} }
```

**Error:**
```json
{ "ok": false, "error": { "code": "ERROR_CODE", "message": "..." } }
```

**Check `response.ok` or `data.ok` before proceeding.**

**Typical error codes:**
- `DUPLICATE_EVENT` — same event_id already accepted (HTTP 409)
- `INVALID_TRANSITION` — invalid state change (HTTP 409)
- `INVALID_TIMESTAMP` — malformed timestamp (HTTP 400). **Note:** The backend expects integer epoch milliseconds for POST /api.events; ISO-8601 strings will be rejected.
- `DUPLICATE_EVENT` — duplicate event ID (HTTP 409)

---

## 7. Deployment Checklist

Before deploying the Member 4 dashboard:

- [ ] Backend running at `http://localhost:8000` (or configured port)
- [ ] `CORS_ORIGINS` in `backend/.env` includes frontend origin
- [ ] WebSocket endpoint `ws://localhost:8000/ws/events` is accessible
- [ ] Backend health check `GET /health` returns `ok: true`
- [ ] Tested: POST /api/events creates event + incident + WebSocket broadcast using **canonical event-v1 shape** (schema_version="event-v1", timestamp as integer epoch milliseconds)
- [ ] Tested: Incident lifecycle (verify → assign → resolve) broadcasts updates
- [ ] Tested: GET /api/crowd returns time-series history
- [ ] Tested: WebSocket reconnect after disconnect
- [ ] Tested: Duplicate event_id returns HTTP 409, not rebroadcast
- [ ] Tested: ISO-8601 timestamps are rejected for POST /api.events (backend validates integer epoch ms)

---

## 8. Integration Notes for Member 4

- **REST is the source of historical/detail data** — use for initial load and individual incident/event lookups
- **WebSocket is for real-time changes** — after initial REST load, WebSocket keeps the UI synchronized
- **Do not rely entirely on WebSockets for history** — REST `/api/events` and `/api/crowd` provide the full historical record
- **Incident state changes are broadcast** — all connected clients receive `incident.updated` when any client calls verify/dismiss/assign/resolve
- **Crowd metrics are time-series** — each event with `people_count` adds a new row; `GET /api/crowd` returns all rows newest-first
- **CORS must be configured** — the backend reads allowed origins from `.env`; do not use `allow_origins=["*"]` in production without justification
- **Canonical event payload**: `POST /api/events` accepts the event-v1 shape. The `timestamp` field **must** be an integer representing Unix epoch milliseconds. ISO-8601 strings will cause a validation error (`INVALID_TIMESTAMP`).
- **WebSocket `event.created`** broadcasts the same canonical payload: `timestamp` is Unix epoch milliseconds; optional fields `track_ids`, `zone_id`, `persistence_ms`, `people_count` may be present.

---

## 8. Appendix: Quick Reference Commands

```bash
# Start backend
uvicorn app.main:app --reload

# Send a fake intrusion event (for testing)
python integration/simulate_member2.py --scenario intrusion

# Check backend health
curl http://localhost:8000/health

# List incidents
curl http://localhost:8000/api/incidents

# List events
curl "http://localhost:8000/api/events?camera_id=CAM_04"

# List crowd history
curl "http://localhost:8000/api/crowd?camera_id=CAM_04"

# Verify incident
curl -X POST http://localhost:8000/api/incidents/{id}/verify \
  -H "Content-Type: application/json" \
  -d '{"user":"operator_01","note":"Confirmed"}'
```

---

## 9. FAQ

Q: The WebSocket connection keeps dropping.
A: The backend auto-broadcasts events; if the process restarts, connections are lost. Reconnect logic in the JavaScript handles this.

Q: I'm not receiving WebSocket messages.
A: Ensure the REST `/api/events` endpoint has been called at least once to trigger event processing. The WebSocket mirrors REST-posted events.

Q: The crowd count isn't updating.
A: Each event with `people_count` creates a new timestamped observation. Multiple events for the same camera append rows, ordered newest-first on `GET /api/crowd`.

Q: I get a CORS error.
A: Add your frontend origin to `backend/.env`: `CORS_ORIGINS=http://localhost:3000` (or `http://localhost:5173`).

Q: Why does the event timestamp look different on the dashboard?
A: The backend stores timestamps as ISO-8601 datetimes in the database, but the **canonical event payload** uses Unix epoch milliseconds. The dashboard formats the epoch ms for display.

--- 

## 10. Integration Checklist for Member 4

- [ ] Backend running at `http://localhost:8000` (or configured port)
- [ ] `CORS_ORIGINS` in `backend/.env` includes frontend origin
- [ ] WebSocket endpoint `ws://localhost:8000/ws/events` is accessible
- [ ] Backend health check `GET /health` returns `ok: true`
- [ ] Tested: POST /api/events creates event using canonical event-v1 shape
- [ ] Tested: Incident lifecycle (verify → assign → resolve) broadcasts updates
- [ ] Tested: GET /api/crowd returns time-series history
- [ ] Tested: WebSocket reconnect after disconnect
- [ ] Tested: Duplicate event_id returns HTTP 409, not rebroadcast
- [ ] Tested: ISO-8601 timestamps are rejected for POST /api.events (backend validates integer epoch ms)
- [ ] Tested: WebSocket `event.created` broadcasts canonical payload with epoch-ms timestamp