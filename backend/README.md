# SIH1349 Railway Intelligence Backend

Member 3 owns the FastAPI backend, SQL database/migrations, incident lifecycle, crowd history, and real-time WebSocket delivery. Member 1/2 AI produces Contract V1 JSON over HTTP; Member 4 consumes REST and WebSocket data. The backend does not import AI runtimes.

## Architecture

```text
Member 1 detection → Member 2 tracking/safety logic → POST /api/events
    → validation → Event + optional Incident/CrowdMetric transaction
    → WebSocket → Member 4 dashboard
```

Contract V1 is frozen in `docs/API_CONTRACT_V1.md`. Python 3.11 is recommended (verified with 3.11.9).

## Clean setup

Run commands from this `backend` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The example environment contains no secrets:

```dotenv
APP_NAME=SIH1349 Railway Intelligence Backend
APP_ENV=development
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./sih1349.db
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=INFO
```

For PostgreSQL, provide an appropriate `DATABASE_URL`; `psycopg2-binary` is included. Do not commit a real `.env`.

## Run and inspect

- Health: `GET http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`
- WebSocket: `ws://localhost:8000/ws/events`
- Fake generator: `python scripts/send_fake_events.py --scenario intrusion`
- Member 2 simulator: `python integration/simulate_member2.py --scenario intrusion`
- HTTP smoke test: `python scripts/smoke_test.py`

## Tests

```powershell
pip install -r requirements-dev.txt
pytest -v
```

Pytest uses `sih1349_test.db`, cleans mutable tables and in-memory dedup state after every test, and only collects Python tests beneath `tests/`.

## LAN testing

Run:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Other private-network devices use `http://<BACKEND_LAN_IP>:8000` and `ws://<BACKEND_LAN_IP>:8000/ws/events`. Add the frontend origin to `CORS_ORIGINS`. Windows Firewall may require allowing TCP port 8000 on private networks. Do not expose this development service publicly.

## Operational safety

- Lists default to 100 records and accept at most 500 through `limit`.
- Event IDs are database-unique; related Event/Incident/CrowdMetric rows commit atomically.
- Evidence fields are references, not image/video bodies; metadata is capped at 64 KiB.
- WebSocket delivery is process-local and best-effort. Clients should reconnect and reload REST history after a backend restart.
- No authentication, authorization, TLS termination, distributed message broker, cloud evidence store, or production rate limiter is included in this hackathon backend.
- Real Member 2 AI/device and Member 4 frontend integration remain team integration tasks.

See `docs/MEMBER2_AI_INTEGRATION.md`, `docs/MEMBER4_FRONTEND_INTEGRATION.md`, and `docs/TEAM_HANDOFF.md`.
