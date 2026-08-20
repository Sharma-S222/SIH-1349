# output.py

import json
from pathlib import Path
from typing import Any


class EventOutput:
    """
    Converts Member 2 safety events into the event-v1
    contract expected at the Member 2 -> Member 3 boundary.
    """

    SCHEMA_VERSION = "1.0"

    def __init__(self, output_dir="outputs/events"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_event(
        self,
        event_type: str,
        camera_id: str,
        timestamp_ms: int,
        track_ids: list[int],
        zone_id: str | None,
        confidence: float,
        severity: str,
        persistence_ms: int,
        metadata: dict[str, Any] | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:

        if not event_type:
            raise ValueError("event_type is required")

        if not camera_id:
            raise ValueError("camera_id is required")

        if timestamp_ms < 0:
            raise ValueError("timestamp_ms cannot be negative")

        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if persistence_ms < 0:
            raise ValueError("persistence_ms cannot be negative")

        if not isinstance(track_ids, list):
            raise TypeError("track_ids must be a list")

        if metadata is None:
            metadata = {}

        if event_id is None:
            event_id = self._generate_event_id(
                camera_id=camera_id,
                timestamp_ms=timestamp_ms,
                track_ids=track_ids,
            )

        event = {
            "schema_version": self.SCHEMA_VERSION,

            "event_id": event_id,

            "camera_id": camera_id,

            "timestamp_ms": timestamp_ms,

            "event_type": event_type,

            "severity": severity,

            "confidence": round(
                float(confidence),
                4,
            ),

            "track_ids": [
                int(track_id)
                for track_id in track_ids
            ],

            "zone_id": zone_id,

            "persistence_ms": int(
                persistence_ms
            ),

            "metadata": metadata,
        }

        return event

    def to_json(
        self,
        event: dict[str, Any],
    ) -> str:

        return json.dumps(
            event,
            indent=2,
            ensure_ascii=False,
        )

    def save(
        self,
        event: dict[str, Any],
        filename: str | None = None,
    ) -> Path:

        if filename is None:
            filename = f"{event['event_id']}.json"

        output_path = (
            self.output_dir / filename
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                event,
                file,
                indent=2,
                ensure_ascii=False,
            )

        return output_path

    @staticmethod
    def _generate_event_id(
        camera_id: str,
        timestamp_ms: int,
        track_ids: list[int],
    ) -> str:

        track_part = "-".join(
            str(track_id)
            for track_id in track_ids
        )

        if not track_part:
            track_part = "none"

        return (
            f"EVT_"
            f"{camera_id}_"
            f"{timestamp_ms}_"
            f"{track_part}"
        )