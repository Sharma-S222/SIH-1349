import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from app.config import settings
from app.utils.log import setup_logging
from app.websocket.manager import manager

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Backend startup: environment=%s", settings.app_env)
    yield
    logger.info("Backend shutdown")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="SIH1349 - AI-based Railway CCTV Intelligence System - Backend",
    lifespan=lifespan,
)

# CORS configuration from environment
allowed_origins = settings.cors_origins if settings.cors_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler that returns Contract V1 error format.
    
    FastAPI default wraps errors in {"detail": ...}, but Contract V1 requires
    {"ok": false, "error": {"code": "...", "message": "..."}}.
    """
    status_code = exc.status_code
    detail = exc.detail
    if isinstance(detail, dict):
        if "error" in detail:
            return JSONResponse(
                status_code=status_code,
                content={"ok": detail.get("ok", False), "error": detail["error"]},
            )
        if "code" in detail:
            return JSONResponse(
                status_code=status_code,
                content={"ok": False, "error": {"code": detail["code"], "message": detail.get("message", str(exc))}},
            )

    return JSONResponse(
        status_code=status_code,
        content={"ok": False, "error": {"code": "HTTP_ERROR", "message": str(detail)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    timestamp_error = any(error.get("loc", ())[-1:] == ("timestamp",) for error in exc.errors())
    code = "INVALID_TIMESTAMP" if timestamp_error else "VALIDATION_ERROR"
    message = "timestamp must be a valid ISO-8601 timezone-aware datetime" if timestamp_error else "request validation failed"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"ok": False, "error": {"code": code, "message": message}},
    )


@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    """Return unexpected failures in Contract V1 error format."""
    logger.exception("Unexpected backend failure", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"ok": False, "error": {"code": "INTERNAL_ERROR", "message": str(exc)}},
    )


@app.get("/health", summary="Health check", description="Backend readiness check")
async def health():
    return {"ok": True, "data": {"status": "ready"}}


# Include API routers
from app.api.events import router as events_router
from app.api.incidents import router as incidents_router
app.include_router(events_router, prefix="/api", tags=["events"])
app.include_router(incidents_router, prefix="/api", tags=["incidents"])


# WebSocket endpoint for real-time event streaming
@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for real-time event broadcasting."""
    await manager.connect(websocket)
    try:
        # Keep connection alive; broadcast events will push data to client
        while True:
            # Wait for messages from client (keep-alive ping/pong or any text)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
