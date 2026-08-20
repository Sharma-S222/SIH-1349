"""Small resilient Contract V1 client for Member 2 event producers."""

from __future__ import annotations

import json
import socket
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def generate_event_id() -> str:
    """Return a restart-safe event identifier."""
    return f"EVT_{uuid.uuid4()}"


def utc_timestamp_epoch_ms() -> int:
    """Return the current Unix epoch time in milliseconds UTC.

    This is the canonical timestamp format for event-v1 payloads.
    Contrast with utc_timestamp() which returns ISO-8601 strings for
    query filters and internal database storage.
    """
    return int(time.time() * 1000)


def utc_timestamp() -> str:
    """Return a timezone-aware ISO-8601 UTC timestamp using the accepted Z form.

    Used for query filters (start_time/end_time) and internal database
    representation, NOT for event payload timestamps.
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _error_code(payload: dict[str, Any] | None) -> str | None:
    return payload.get("error", {}).get("code") if payload else None


def _message(payload: dict[str, Any] | None, fallback: Any) -> str:
    return str(payload.get("error", {}).get("message", fallback)) if payload else str(fallback)


@dataclass(frozen=True)
class EventSendResult:
    accepted: bool
    status_code: int | None
    response: dict[str, Any] | None
    error: str | None = None
    duplicate: bool = False


class BackendEventClient:
    """POST Contract V1 events without crashing a continuous producer loop."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 5.0, retries: int = 1):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if retries not in (0, 1):
            raise ValueError("retries must be 0 or 1")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/api/events"

    def send_event(self, event: Mapping[str, Any]) -> EventSendResult:
        """Send one event and return an explicit result for every outcome."""
        body = json.dumps(dict(event), separators=(",", ":")).encode("utf-8")
        request = Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )

        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    payload = self._decode(response.read())
                    return EventSendResult(True, response.status, payload)
            except HTTPError as exc:
                payload = self._decode(exc.read())
                duplicate = exc.code == 409 and self._error_code(payload) == "DUPLICATE_EVENT"
                return EventSendResult(False, exc.code, payload, self._message(payload, exc.reason), duplicate)
            except (URLError, TimeoutError, socket.timeout, OSError) as exc:
                if attempt < self.retries:
                    time.sleep(0.2)
                    continue
                return EventSendResult(False, None, None, f"network failure: {exc}")
            except (TypeError, ValueError) as exc:
                return EventSendResult(False, None, None, f"event serialization failed: {exc}")

        return EventSendResult(False, None, None, "event request failed")


    @staticmethod
    def _decode(raw: bytes) -> dict[str, Any] | None:
        if not raw:
            return None
        try:
            value = json.loads(raw.decode("utf-8"))
            return value if isinstance(value, dict) else {"data": value}
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {"error": {"code": "INVALID_RESPONSE", "message": "backend returned non-JSON data"}}


    @staticmethod
    def _error_code(payload: dict[str, Any] | None) -> str | None:
        return payload.get("error", {}).get("code") if payload else None


    @staticmethod
    def _message(payload: dict[str, Any] | None, fallback: Any) -> str:
        return str(payload.get("error", {}).get("message", fallback)) if payload else str(fallback)