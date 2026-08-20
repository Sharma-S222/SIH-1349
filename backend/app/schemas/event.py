import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class Evidence(BaseModel):
    snapshot_path: Optional[str] = Field(None, max_length=2048, description="Path to image snapshot (relative or URL)")
    clip_path: Optional[str] = Field(None, max_length=2048, description="Path to video clip (relative or URL)")


class AIEvent(BaseModel):
    """Canonical event-v1 schema-compliant event model.

    This model validates events against the repository-level contract at
    docs/contracts/event-v1.schema.json.
    """

    schema_version: str = Field(
        ...,
        description="Canonical schema version identifier. Must be 'event-v1'.",
    )
    event_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique event identifier",
    )
    camera_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Camera identifier",
    )
    timestamp: int = Field(
        ...,
        ge=0,
        description="Unix epoch milliseconds UTC (e.g. 1787218200000)",
    )
    event_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type of event, e.g. crowding, intrusion, loitering",
    )
    severity: str = Field(
        ...,
        description="Severity level. Use uppercase: LOW, MEDIUM, HIGH, CRITICAL",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Event confidence score",
    )
    track_ids: Optional[List[str]] = Field(
        None,
        description="Optional track identifiers associated with the event",
    )
    zone_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional zone identifier",
    )
    persistence_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Optional persistence duration in milliseconds",
    )
    people_count: Optional[int] = Field(
        None,
        ge=0,
        description="Optional people count from crowd analysis",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional extensible metadata (do not move explicit contract fields here)",
    )
    evidence: Evidence = Field(
        default_factory=Evidence,
        description="Optional snapshot and clip path references",
    )

    @validator("schema_version")
    def validate_schema_version(cls, v: str) -> str:
        if v != "event-v1":
            raise ValueError("schema_version must be 'event-v1'")
        return v

    @validator("timestamp")
    def validate_epoch_milliseconds(cls, v: int) -> int:
        """Validate that timestamp is a non-negative integer (Unix epoch milliseconds).

        Accepts int values directly. Rejects strings, floats, or negative numbers.
        """
        if not isinstance(v, int):
            raise ValueError("timestamp must be an integer (Unix epoch milliseconds)")
        if v < 0:
            raise ValueError("timestamp must be non-negative (Unix epoch milliseconds in UTC)")
        return v

    @validator("metadata")
    def validate_metadata_size(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if len(json.dumps(value, separators=(",", ":"), default=str).encode("utf-8")) > 65_536:
            raise ValueError("metadata must not exceed 64 KiB when JSON encoded")
        return value