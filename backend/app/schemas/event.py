import json
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Evidence(BaseModel):
    snapshot_path: Optional[str] = Field(None, max_length=2048)
    clip_path: Optional[str] = Field(None, max_length=2048)


class AIEvent(BaseModel):
    schema_version: str = Field(..., min_length=1, max_length=20, description="Schema version, e.g. '1.0'")
    event_id: str = Field(..., min_length=1, max_length=100, description="Unique event identifier")
    camera_id: str = Field(..., min_length=1, max_length=50, description="Camera identifier, e.g. 'CAM_04'")
    timestamp: str = Field(..., description="ISO-8601 formatted timestamp (timezone-aware)")
    event_type: str = Field(..., min_length=1, max_length=100, description="Type of event")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    zone_id: Optional[str] = Field(None, max_length=100, description="Zone identifier, optional per event type")
    people_count: Optional[int] = Field(None, ge=0, description="People count, optional")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional structured AI metadata")
    evidence: Evidence = Field(default_factory=Evidence)

    @field_validator("metadata")
    @classmethod
    def validate_metadata_size(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if len(json.dumps(value, separators=(",", ":"), default=str).encode("utf-8")) > 65_536:
            raise ValueError("metadata must not exceed 64 KiB when JSON encoded")
        return value

    @field_validator("timestamp")
    @classmethod
    def validate_iso_timestamp(cls, v: str) -> str:
        """Validate and normalise ISO-8601 timestamp.

        Accepts both offset form (e.g. '2026-08-20T09:30:00+05:30')
        and Z-suffix form (e.g. '2026-08-20T04:00:00Z').
        Raises ValueError if the string cannot be parsed as a
        timezone-aware datetime.
        """
        normalised = v.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalised)
        except (ValueError, TypeError):
            raise ValueError(
                "timestamp must be a valid ISO-8601 timezone-aware datetime "
                "(e.g. '2026-08-20T09:30:00+05:30' or '2026-08-20T04:00:00Z')"
            )
        # Reject naive (no timezone) datetimes
        if parsed.tzinfo is None:
            raise ValueError(
                "timestamp must include a timezone offset "
                "(e.g. '+05:30' or 'Z')"
            )
        return v


EventCreate = AIEvent
