# SIH1349 Team Handoff

## Member 2 — Tracking and safety logic

Send frozen Contract V1 JSON to `POST /api/events`. Follow `MEMBER2_AI_INTEGRATION.md`; do not import AI code into the backend.

```powershell
python integration/simulate_member2.py --scenario intrusion
python integration/simulate_member2.py --scenario crowd-overload
```

Use UUID event IDs, timezone-aware timestamps, normalized confidence, centralized event-type mapping, and producer-side correlation/cooldowns for persistent detections.

## Member 4 — Dashboard

Use:

- `GET /api/events`
- `GET /api/incidents`
- `GET /api/crowd`
- `POST /api/incidents/{id}/verify`
- `POST /api/incidents/{id}/dismiss`
- `POST /api/incidents/{id}/assign`
- `POST /api/incidents/{id}/resolve`
- `WS /ws/events`

Message types remain `connection-established`, `event.created`, `crowd.updated`, and `incident.updated`. Follow `MEMBER4_FRONTEND_INTEGRATION.md` and the frozen `API_CONTRACT_V1.md`.

## Member 5 — Deployment and environment

- Recommended Python: 3.11 (verified 3.11.9).
- Working directory: `backend`.
- Install: `pip install -r requirements.txt`.
- Environment: copy `.env.example` to `.env` and adjust only documented settings.
- Migrations: `alembic upgrade head`.
- Startup: `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
- Default backend port: 8000.
- CORS: comma-separated frontend origins in `CORS_ORIGINS`.

For same-LAN testing, bind `0.0.0.0`; clients use `http://<BACKEND_LAN_IP>:8000` and `ws://<BACKEND_LAN_IP>:8000/ws/events`. Windows Firewall may need TCP 8000 allowed on the private network. Do not expose the service publicly. Docker is intentionally not introduced.

## Member 6 — Testing

```powershell
pip install -r requirements-dev.txt
pytest -v
python scripts/smoke_test.py --backend-url http://localhost:8000
```

The smoke script deterministically checks health, event ingestion/history, safety-incident creation, and crowd history. Tests use a separate database and do not collect old text logs.

## Network quick reference

| Situation | REST base | WebSocket |
|---|---|---|
| Same machine | `http://localhost:8000` | `ws://localhost:8000/ws/events` |
| Same private LAN | `http://<BACKEND_LAN_IP>:8000` | `ws://<BACKEND_LAN_IP>:8000/ws/events` |
