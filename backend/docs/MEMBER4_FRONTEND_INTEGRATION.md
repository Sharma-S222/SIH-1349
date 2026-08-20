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
```

**Requirements:**
- Automatic reconnect on disconnect
- Avoid creating unlimited reconnect timers (use setTimeout with delay)
- Handle malformed messages safely (try/catch around JSON.parse)
- Do not crash UI when backend temporarily disconnects

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

## 4. event.created Handling

When a new event is created, the dashboard should:

```javascript
function handleEventCreated(eventData) {
  const { event_id, camera_id, event_type, severity, confidence, timestamp } = eventData;

  // Add event alert/card
  addEventAlert({
    id: event_id,
    camera: camera_id,
    type: event_type,
    severity: severity,
    confidence: confidence,
    time: timestamp,
  });

  // Optionally fetch full REST detail if needed
  // fetch(`http://localhost:8000/api/events/${event_id}`);

  // Highlight HIGH/CRITICAL severity appropriately
  if (severity === 'HIGH' || severity === 'CRITICAL') {
    highlightCriticalEvent(event_id);
  }
}
```

**Key actions:**
- Add event alert/card to dashboard
- Optionally fetch full REST detail if needed
- Highlight HIGH/CRITICAL severity appropriately

---

## 5. incident.updated Handling

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

## 6. crowd.updated Handling

When crowd metrics update:

```javascript
function handleCrowdUpdated(crowdData) {
  const { camera_id, zone_id, people_count, timestamp } = crowdData;

  // Update crowd count display
  updateCrowdCount(camera_id, people_count);

  // Update timestamp display
  updateCrowdTimestamp(camera_id, timestamp);

  // Optionally update chart data
  // chartData[camera_id].push({ people_count, timestamp });
  // chart.redraw();
}
```

**Key actions:**
- Update crowd count display
- Update timestamp display
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

**Check `response.ok` or `data.ok` before proceeding.** Never assume success without checking.

**Typical error codes:**
- `DUPLICATE_EVENT` — same event_id already accepted (HTTP 409)
- `INVALID_TRANSITION` — invalid state change (HTTP 409)
- `INVALID_TIMESTAMP` — malformed timestamp (HTTP 400)
- `DUPLICATE_EVENT` — duplicate event ID (HTTP 409)

---

## 8. Deployment Checklist

Before deploying the Member 4 dashboard:

- [ ] Backend running at `http://localhost:8000` (or configured port)
- [ ] `CORS_ORIGINS` in `backend/.env` includes frontend origin
- [ ] WebSocket endpoint `ws://localhost:8000/ws/events` is accessible
- [ ] Backend health check `GET /health` returns `ok: true`
- [ ] Tested: POST /api/events creates event + incident + WebSocket broadcast
- [ ] Tested: Incident lifecycle (verify → assign → resolve) broadcasts updates
- [ ] Tested: GET /api/crowd returns time-series history
- [ ] Tested: WebSocket reconnect after disconnect
- [ ] Tested: Duplicate event_id returns HTTP 409, not rebroadcast

---

## 9. Frequently Asked Questions

**Q: The WebSocket connection keeps dropping.**
A: The backend auto-broadcasts events; if the process restarts, connections are lost. Reconnect logic in the JavaScript handles this.

Q: I'm not receiving WebSocket messages.
A: Ensure the REST `/api/events` endpoint has been called at least once to trigger event processing. The WebSocket mirrors REST-posted events.

Q: The crowd count isn't updating.
A: Each event with `people_count` creates a new timestamped observation. Multiple events for the same camera append rows, ordered newest-first on `GET /api/crowd`.

Q: I get a CORS error.
A. Add your frontend origin to `backend/.env`: `CORS_ORIGINS=http://localhost:3000` (or `http://localhost:5173`).

---

## 10. Integration Notes for Member 4

- **REST is the source of historical/detail data** — use for initial load and individual incident/event lookups
- **WebSocket is for real-time changes** — after initial REST load, WebSocket keeps the UI synchronized
- **Do not rely entirely on WebSockets for history** — REST `/api/events` and `/api/crowd` provide the full historical record
- **Incident state changes are broadcast** — all connected clients receive `incident.updated` when any client calls verify/dismiss/assign/resolve
- **Crowd metrics are time-series** — each event with `people_count` adds a new row; `GET /api/crowd` returns all rows newest-first
- **CORS must be configured** — the backend reads allowed origins from `.env`; do not use `allow_origins=["*"]` in production without justification

---

## Appendix: Quick Reference Commands

```bash
# Start backend
uvicorn app.main:app --reload

# Send a fake intrusion event (for testing)
python scripts/send_fake_events.py --scenario intrusion

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