"""
pytest configuration for SIH1349 backend tests.

Key design decisions:
- Uses a separate file-based SQLite DB (sih1349_test.db) so tests never
  touch the development database (sih1349.db).
- DATABASE_URL env var is patched BEFORE any app modules are imported so
  that app.database picks up the test URL.
- Cleans ALL mutable tables after every test for full isolation.
- Resets in-memory dedup sets (accepted_event_ids, accepted_incident_ids)
  after every test.
"""

import os

# ── Override database URL to the test DB BEFORE importing the app ──────
# This must happen before any app.* import so that app.database.engine
# points at the test database, not the production one.
os.environ["DATABASE_URL"] = "sqlite:///./sih1349_test.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import engine, Base, SessionLocal


# Create all tables in the test database once per session
Base.metadata.create_all(engine)


@pytest.fixture(autouse=True, scope="function")
def db_cleanup():
    """Clean up ALL data after each test for full isolation."""
    yield

    # Remove all data from all mutable tables in reverse FK order
    db = SessionLocal()
    try:
        from app.models import OperatorAction, Incident, Event, CrowdMetric
        for model in [OperatorAction, Incident, Event, CrowdMetric]:
            db.query(model).delete()
        db.commit()
    finally:
        db.close()

    # Reset process-level dedup state so tests never bleed into each other
    import app.api.events as events_module
    import app.api.incidents as incidents_module
    events_module.accepted_event_ids = set()
    incidents_module.accepted_incident_ids = set()


# Shared test client (reused across all test modules via conftest)
client = TestClient(app)