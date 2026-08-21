import time
import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.websocket.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()

class FrameBroker:
    def __init__(self):
        self.latest_frames: Dict[str, bytes] = {}
        self.latest_telemetry: Dict[str, Dict[str, Any]] = {}
        self.last_updated: Dict[str, float] = {}

broker = FrameBroker()

@router.post("/{camera_id}/frame")
async def receive_frame(camera_id: str, request: Request):
    """Receive JPEG frame from pipeline."""
    body = await request.body()
    broker.latest_frames[camera_id] = body
    broker.last_updated[camera_id] = time.time()
    return {"ok": True}

@router.post("/{camera_id}/telemetry")
async def receive_telemetry(camera_id: str, payload: dict):
    """Receive JSON telemetry from pipeline and broadcast."""
    payload["timestamp_local"] = time.time()
    broker.latest_telemetry[camera_id] = payload
    broker.last_updated[camera_id] = time.time()
    
    await manager.broadcast({
        "type": "camera.telemetry",
        "camera_id": camera_id,
        "data": payload
    })
    return {"ok": True}

async def frame_generator(camera_id: str):
    """Generate multipart JPEG stream."""
    while True:
        frame = broker.latest_frames.get(camera_id)
        if frame:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        # 10 fps max for stream update checks, effectively bounds streaming bandwidth
        await asyncio.sleep(0.1)

@router.get("")
async def list_cameras():
    cameras = []
    now = time.time()
    for cam_id, tel in broker.latest_telemetry.items():
        is_stale = (now - broker.last_updated.get(cam_id, 0)) > 5.0
        cameras.append({"camera_id": cam_id, "status": "OFFLINE" if is_stale else "ONLINE", "people_count": tel.get("people_count", 0), "telemetry": tel})
    return {"ok": True, "data": cameras}

@router.get("/{camera_id}/stream")
async def stream_camera(camera_id: str):
    return StreamingResponse(
        frame_generator(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


