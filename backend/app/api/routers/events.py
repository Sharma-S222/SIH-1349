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
            query = query.filter(Event.timestamp >= start_time)
        if end_time:
            query = query.filter(Event.timestamp <= end_time)

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
                    "timestamp": str(e.timestamp),
                    "zone_id": e.zone_id,
                    "people_count": e.people_count,
                }
                for e in results
            ],
        }
    finally:
        db.close()


@router.post(
    "/events",
    summary="Accept AI event",
    description="Receive and process an AI-generated event.",
)
async def create_event(event: AIEvent):
    """Process incoming AI event with validation, persistence, and broadcasting."""
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

    # 2. Store event in database
    db = SessionLocal()
    try:
        db_event = Event(
            event_id=event.event_id,
            schema_version=event.schema_version,
            camera_id=event.camera_id,
            event_type=event.event_type,
            severity=event.severity,
            confidence=event.confidence,
            timestamp=event.timestamp,
            zone_id=event.zone_id,
            people_count=event.people_count,
            raw_metadata=str(event.metadata) if event.metadata else "{}",
            snapshot_path=event.evidence.snapshot_path if event.evidence else None,
            clip_path=event.evidence.clip_path if event.evidence else None,
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)

        # 3. Update crowd metric if people_count exists
        from app.models import CrowdMetric

        # Check if there's already a metric for this camera + zone
        stmt = select(CrowdMetric).filter(
            CrowdMetric.camera_id == event.camera_id
        )
        if event.zone_id:
            stmt = stmt.filter(CrowdMetric.zone_id == event.zone_id)

        metric = db.execute(stmt).scalar_one_or_none()

        if metric:
            metric.people_count = event.people_count
            metric.timestamp = event.timestamp
        else:
            new_metric = CrowdMetric(
                camera_id=event.camera_id,
                zone_id=event.zone_id,
                people_count=event.people_count,
                timestamp=event.timestamp,
            )
            db.add(new_metric)

        db.commit()

        # 4. Broadcast via WebSocket
        broadcast_data = {
            "type": "event.created",
            "data": {
                "event_id": db_event.event_id,
                "camera_id": db_event.camera_id,
                "event_type": db_event.event_type,
                "severity": db_event.severity,
                "confidence": db_event.confidence,
                "timestamp": str(db_event.timestamp),
            },
        }
        manager.broadcast(broadcast_data)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {"ok": True, "data": {"event_id": db_event.event_id}}