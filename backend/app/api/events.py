import json
import logging
from datetime import datetime as _dt

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database import SessionLocal
from app.models import CrowdMetric, Event, Incident
from app.schemas.event import AIEvent
from app.websocket.manager import manager

router = APIRouter(tags=["events"])
logger = logging.getLogger(__name__)

SAFETY_EVENT_TYPES = {
    "restricted_zone_intrusion",
    "fall_detected",
    "abandoned_object",
    "violence_detected",
    "crowd_overload",
    "fire_or_smoke",
}

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
    limit: int = Query(100, ge=1, le=500),
):
    """Return event history with optional filtering."""
    db = SessionLocal()
    try:
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


@router.get(
    "/crowd",
    summary="Get crowd history",
    description="Return crowd metrics history with optional filtering.",
)
async def crowd_history(
    camera_id: str = None,
    zone_id: str = None,
    start_time: str = None,
    end_time: str = None,
    limit: int = Query(100, ge=1, le=500),
):
    """Return crowd metrics history with optional filtering."""
    db = SessionLocal()
    try:
        query = select(CrowdMetric)

        if camera_id:
            query = query.filter(CrowdMetric.camera_id == camera_id)
        if zone_id:
            query = query.filter(CrowdMetric.zone_id == zone_id)
        if start_time:
            query = query.filter(CrowdMetric.timestamp >= start_time)
        if end_time:
            query = query.filter(CrowdMetric.timestamp <= end_time)

        query = query.order_by(CrowdMetric.timestamp.desc()).limit(limit)
        results = db.execute(query).scalars().all()

        return {
            "ok": True,
            "data": [
                {
                    "camera_id": m.camera_id,
                    "zone_id": m.zone_id,
                    "people_count": m.people_count,
                    "timestamp": str(m.timestamp),
                }
                for m in results
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
    # Fast rejection is only an optimization; the database unique constraint is
    # the authoritative protection, including across workers and restarts.
    if event.event_id in accepted_event_ids:
        logger.info("Duplicate event rejected: event_id=%s", event.event_id)
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
    parsed_timestamp = _dt.fromisoformat(event.timestamp.replace("Z", "+00:00"))
    db = SessionLocal()
    try:
        db_event = Event(
            event_id=event.event_id,
            schema_version=event.schema_version,
            camera_id=event.camera_id,
            event_type=event.event_type,
            severity=event.severity,
            confidence=event.confidence,
            timestamp=parsed_timestamp,
            zone_id=event.zone_id,
            people_count=event.people_count,
            raw_metadata=json.dumps(event.metadata, separators=(",", ":")),
            snapshot_path=event.evidence.snapshot_path if event.evidence else None,
            clip_path=event.evidence.clip_path if event.evidence else None,
        )
        db.add(db_event)
        if event.people_count is not None:
            db.add(CrowdMetric(
                camera_id=event.camera_id,
                zone_id=event.zone_id,
                people_count=event.people_count,
                timestamp=parsed_timestamp,
            ))

        if event.event_type in SAFETY_EVENT_TYPES:
            db.add(Incident(event_id=event.event_id, status="NEW"))

        # Event, crowd observation, and incident are one atomic transaction.
        db.commit()
        db.refresh(db_event)
    except IntegrityError:
        db.rollback()
        logger.info("Duplicate event rejected by database: event_id=%s", event.event_id)
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
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database failure while persisting event_id=%s", event.event_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"ok": False, "error": {"code": "DATABASE_ERROR", "message": "event could not be persisted"}},
        )
    finally:
        db.close()

    accepted_event_ids.add(event.event_id)
    logger.info("Event accepted: event_id=%s camera_id=%s type=%s", event.event_id, event.camera_id, event.event_type)
    if event.event_type in SAFETY_EVENT_TYPES:
        logger.info("Incident created: event_id=%s status=NEW", event.event_id)

    await manager.broadcast({
            "type": "event.created",
            "data": {
                "event_id": db_event.event_id,
                "camera_id": db_event.camera_id,
                "event_type": db_event.event_type,
                "severity": db_event.severity,
                "confidence": db_event.confidence,
                "timestamp": str(db_event.timestamp),
            },
        })

    if db_event.people_count is not None:
        await manager.broadcast({
                "type": "crowd.updated",
                "data": {
                    "camera_id": db_event.camera_id,
                    "zone_id": db_event.zone_id if db_event.zone_id is not None else "",
                    "people_count": db_event.people_count,
                    "timestamp": str(db_event.timestamp),
                },
            })

    return {"ok": True, "data": {"event_id": db_event.event_id}}
