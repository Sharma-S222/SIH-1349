from typing import Optional

import logging

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from datetime import datetime
from app.database import SessionLocal
from app.models import Incident, OperatorAction
from app.websocket.manager import manager

router = APIRouter(tags=["incidents"])
logger = logging.getLogger(__name__)

# Track accepted incident IDs
accepted_incident_ids: set = set()

# Valid state transitions
TRANSITIONS = {
    "NEW": {"verify", "dismiss"},
    "VERIFIED": {"assign"},
    "ASSIGNED": {"resolve"},
    "DISMISSED": set(),  # terminal state
    "RESOLVED": set(),   # terminal state
}


# ─── Request body schemas ──────────────────────────────────────────────

class OperatorPayload(BaseModel):
    """Request body for verify / dismiss / resolve actions."""
    user: str = "operator_01"
    note: Optional[str] = None


class AssignPayload(BaseModel):
    """Request body for assign action."""
    assigned_to: str
    user: str = "operator_01"
    note: Optional[str] = None


# ─── Helper ────────────────────────────────────────────────────────────

def _incident_not_found(incident_id: str):
    return JSONResponse(
        status_code=404,
        content={
            "ok": False,
            "error": {
                "code": "INCIDENT_NOT_FOUND",
                "message": f"incident with event_id '{incident_id}' not found",
            },
        },
    )


def _invalid_transition(current_status: str, target: str):
    return JSONResponse(
        status_code=409,
        content={
            "ok": False,
            "error": {
                "code": "INVALID_TRANSITION",
                "message": f"cannot transition from '{current_status}' to '{target}'",
            },
        },
    )


# ─── Routes ────────────────────────────────────────────────────────────

@router.get(
    "/incidents",
    summary="Get incident inbox",
    description="Return incident inbox with optional status filter.",
)
async def list_incidents(status: str = None, limit: int = Query(100, ge=1, le=500)):
    """Return incident inbox with optional status filter."""
    db = SessionLocal()
    try:
        query = select(Incident)

        if status:
            query = query.filter(Incident.status == status)

        query = query.order_by(Incident.created_at.desc()).limit(limit)
        results = db.execute(query).scalars().all()

        return {
            "ok": True,
            "data": [
                {
                    "incident_id": i.id,
                    "event_id": i.event_id,
                    "status": i.status,
                    "assigned_to": i.assigned_to,
                    "created_at": str(i.created_at),
                    "resolved_at": str(i.resolved_at) if i.resolved_at else None,
                }
                for i in results
            ],
        }
    finally:
        db.close()


@router.post(
    "/incidents/{incident_id}/verify",
    summary="Verify incident",
    description="Mark incident as verified. Creates audit record.",
)
async def verify_incident(incident_id: str, payload: OperatorPayload):
    """Mark incident verified with audit trail."""
    db = SessionLocal()
    try:
        stmt = select(Incident).filter(Incident.event_id == incident_id)
        incident = db.execute(stmt).scalar_one_or_none()

        if not incident:
            return _incident_not_found(incident_id)

        current_status = incident.status
        if "verify" not in TRANSITIONS.get(current_status, set()):
            return _invalid_transition(current_status, "VERIFIED")

        incident.status = "VERIFIED"
        db.add(incident)

        action = OperatorAction(
            incident_id=incident.id,
            action="verify",
            user=payload.user,
            note=payload.note,
        )
        db.add(action)
        db.commit()
        logger.info("Incident action: event_id=%s action=verify user=%s", incident_id, payload.user)

        # Broadcast incident.updated per Contract V1
        await manager.broadcast({
            "type": "incident.updated",
            "data": {
                "incident_id": incident.id,
                "status": incident.status,
                "assigned_to": incident.assigned_to,
            },
        })

        return {
            "ok": True,
            "data": {
                "incident_id": incident.id,
                "event_id": incident.event_id,
                "status": incident.status,
            },
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post(
    "/incidents/{incident_id}/dismiss",
    summary="Dismiss incident",
    description="Dismiss false or irrelevant alert. Creates audit record.",
)
async def dismiss_incident(incident_id: str, payload: OperatorPayload):
    """Dismiss incident with audit trail."""
    db = SessionLocal()
    try:
        stmt = select(Incident).filter(Incident.event_id == incident_id)
        incident = db.execute(stmt).scalar_one_or_none()

        if not incident:
            return _incident_not_found(incident_id)

        current_status = incident.status
        if "dismiss" not in TRANSITIONS.get(current_status, set()):
            return _invalid_transition(current_status, "DISMISSED")

        incident.status = "DISMISSED"
        db.add(incident)

        action = OperatorAction(
            incident_id=incident.id,
            action="dismiss",
            user=payload.user,
            note=payload.note,
        )
        db.add(action)
        db.commit()
        logger.info("Incident action: event_id=%s action=dismiss user=%s", incident_id, payload.user)

        await manager.broadcast({
            "type": "incident.updated",
            "data": {
                "incident_id": incident.id,
                "status": incident.status,
                "assigned_to": incident.assigned_to,
            },
        })

        return {
            "ok": True,
            "data": {
                "incident_id": incident.id,
                "event_id": incident.event_id,
                "status": incident.status,
            },
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post(
    "/incidents/{incident_id}/assign",
    summary="Assign incident",
    description="Assign incident to operator/team. Creates audit record.",
)
async def assign_incident(incident_id: str, payload: AssignPayload):
    """Assign incident to operator/team with audit trail."""
    db = SessionLocal()
    try:
        stmt = select(Incident).filter(Incident.event_id == incident_id)
        incident = db.execute(stmt).scalar_one_or_none()

        if not incident:
            return _incident_not_found(incident_id)

        current_status = incident.status
        if "assign" not in TRANSITIONS.get(current_status, set()):
            return _invalid_transition(current_status, "ASSIGNED")

        incident.status = "ASSIGNED"
        incident.assigned_to = payload.assigned_to
        db.add(incident)

        action = OperatorAction(
            incident_id=incident.id,
            action="assign",
            user=payload.user,
            note=payload.note,
        )
        db.add(action)
        db.commit()
        logger.info("Incident action: event_id=%s action=assign user=%s", incident_id, payload.user)

        await manager.broadcast({
            "type": "incident.updated",
            "data": {
                "incident_id": incident.id,
                "status": incident.status,
                "assigned_to": incident.assigned_to,
            },
        })

        return {
            "ok": True,
            "data": {
                "incident_id": incident.id,
                "event_id": incident.event_id,
                "status": incident.status,
                "assigned_to": incident.assigned_to,
            },
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post(
    "/incidents/{incident_id}/resolve",
    summary="Resolve incident",
    description="Resolve/close incident. Creates audit record.",
)
async def resolve_incident(incident_id: str, payload: OperatorPayload):
    """Resolve incident with audit trail."""
    db = SessionLocal()
    try:
        stmt = select(Incident).filter(Incident.event_id == incident_id)
        incident = db.execute(stmt).scalar_one_or_none()

        if not incident:
            return _incident_not_found(incident_id)

        current_status = incident.status
        if "resolve" not in TRANSITIONS.get(current_status, set()):
            return _invalid_transition(current_status, "RESOLVED")

        incident.status = "RESOLVED"
        incident.resolved_at = datetime.now()
        db.add(incident)

        action = OperatorAction(
            incident_id=incident.id,
            action="resolve",
            user=payload.user,
            note=payload.note,
        )
        db.add(action)
        db.commit()
        logger.info("Incident action: event_id=%s action=resolve user=%s", incident_id, payload.user)

        await manager.broadcast({
            "type": "incident.updated",
            "data": {
                "incident_id": incident.id,
                "status": incident.status,
                "assigned_to": incident.assigned_to,
            },
        })

        return {
            "ok": True,
            "data": {
                "incident_id": incident.id,
                "event_id": incident.event_id,
                "status": incident.status,
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            },
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
