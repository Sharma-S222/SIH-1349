from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Event, CrowdMetric
from app.schemas.event import AIEvent
from app.websocket.manager import manager

router = APIRouter(prefix="/api", tags=["events"])

# Track accepted event IDs (per-process, simple demo)
accepted_event_ids: set = set()


@router.get(
    "/events",
    summary="Get event history",
    description="Return event history with optional filters.",
)
async def list_events(
    camera_id: str = None,
    event_type: str = None,
    severity: str = None,
    start_time: str = None,
    end_time: str = None,
    limit: int = 100,
):
    """Return event history with optional filtering."""
    db = SessionLocal()
    try:
        from sqlalchemy import select

        query = select(Event)

        if camera_id:
            query = query.filter(Event.camera_id == camera_id)
        if event_type:
            query = query.filter(Event.event_type == event_type)
        if severity:
            query = query.filter(Event.severity == severity)
        if start_time:
            # start_time may be ISO-8601 from query params; convert to comparable
            # For now, treat as epoch ms string and compare as string for simplicity
            query = query.filter(Event.timestamp >= func.cast(start_time, DateTime))
        if end_time:
            query = query.filter(Event.timestamp <= func.cast(end_time, DateTime))

        query = query.order_by(Event.timestamp.desc()).limit(limit)
        results = db.execute(query).scalars().all()

        return {
            "ok": True,
            "data": [
                {
                    "event_id": e.event_id,
                    "camera_id": e.camera_id,
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "confidence": e.confidence,
                    "timestamp": (
                        e.timestamp.isoformat() if isinstance(e.timestamp, datetime) else str(e.timestamp)
                    ),
                    "zone_id": e.zone_id,
                    "people_count": e.people_count,
                    "track_ids": e.track_ids,
                    "persistence_ms": e.persistence_ms,
                }
                for e in results
            ],
        }
    finally:
        db.close()


@router.post(
    "/events",
    summary="Accept AI event",
    description="Receive and process an AI-generated event validated against canonical event-v1 schema.",
)
async def create_event(event: AIEvent):
    """Process incoming AI event with validation, persistence, and broadcasting.

    Expected payload (canonical event-v1 shape):
    {
        "schema_version": "event-v1",
        "event_id": "EVT_000123",
        "camera_id": "CAM_PLATFORM_01",
        "timestamp": 1787218200000,  # integer epoch milliseconds UTC
        "event_type": "restricted_zone_intrusion",
        "severity": "HIGH",
        "confidence": 0.92,
        "track_ids": ["17"],           # optional
        "zone_id": "ZONE_PLATFORM_EDGE",  # optional
        "persistence_ms": 2200,         # optional, integer >= 0
        "people_count": 1,              # optional, integer >= 0
        "evidence": {"snapshot_path": None, "clip_path": None},  # optional
        "metadata": {}                  # optional extensible object
    }
    """
    global accepted_event_ids

    # 1. Check for duplicate event_id
    if event.event_id in accepted_event_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "ok": False,
                "error": {
                    "code": "DUPLICATE_EVENT",
                    "message": f"event_id '{event.event_id}' already accepted",
                },
            },
        )
    accepted_event_ids.add(event.event_id)

    # 2. Convert epoch milliseconds timestamp to datetime for DB storage
    from datetime import datetime, timezone
    try:
        dt = datetime.fromtimestamp(event.timestamp / 1000.0, tz=timezone.utc)
    except (ValueError, OSError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "ok": False,
                "error": {
                    "code": "INVALID_TIMESTAMP",
                    "message": f"invalid epoch milliseconds timestamp: {e}",
                },
            },
        )

    # 3. Store event in database
    db = SessionLocal()
    try:
        db_event = Event(
            event_id=event.event_id,
            schema_version=event.schema_version,
            camera_id=event.camera_id,
            event_type=event.event_type,
            severity=event.severity,
            confidence=event.confidence,
            timestamp=dt,
            zone_id=event.zone_id,
            people_count=event.people_count,
            track_ids=event.track_ids,
            persistence_ms=event.persistence_ms,
            raw_metadata=json.dumps(event.metadata) if event.metadata else "{}",
            snapshot_path=event.evidence.snapshot_path if event.evidence else None,
            clip_path=event.evidence.clip_path if event.evidence else None,
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)

        # 3. Update crowd metric if people_count exists
        from app.models import CrowdMetric

        # Check if there's already a metric for this camera + zone
        stmt = select(CrowdMetric).filter(CrowdMetric.camera_id == event.camera_id)
        if event.zone_id:
            stmt = stmt.filter(CrowdMetric.zone_id == event.zone_id)

        metric = db.execute(stmt).scalar_one_or_none()

        if metric:
            metric.people_count = event.people_count
            metric.timestamp = dt
        else:
            new_metric = CrowdMetric(
                camera_id=event.camera_id,
                zone_id=event.zone_id,
                people_count=event.people_count,
                timestamp=dt,
            )
            db.add(new_metric)

        db.commit()

        # 4. Broadcast via WebSocket (use epoch milliseconds timestamp)
        broadcast_data = {
            "type": "event.created",
            "data": {
                "event_id": db_event.event_id,
                "camera_id": db_event.camera_id,
                "event_type": db_event.event_type,
                "severity": db_event.severity,
                "confidence": db_event.confidence,
                "timestamp": event.timestamp,  # send epoch ms as canonical
            },
        }
        if event.track_ids is not None:
            broadcast_data["data"]["track_ids"] = event.track_ids
        if event.zone_id is not None:
            broadcast_data["data"]["zone_id"] = event.zone_id
        if event.persistence_ms is not None:
            broadcast_data["data"]["persistence_ms"] = event.persistence_ms
        if event.people_count is not None:
            broadcast_data["data"]["people_count"] = event.people_count

        manager.broadcast(broadcast_data)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {"ok": True, "data": {"event_id": db_event.event_id}}