import json
from pathlib import Path
from typing import Any

from events import SafetyEvent


class EventOutput:
    """
    Converts SafetyEvent objects into the canonical JSON
    representation used by downstream systems and storage.
    """

    SCHEMA_VERSION = "1.1"

    def __init__(
        self,
        output_dir: str = "outputs/events",
    ):
        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def build_event(
        self,
        event: SafetyEvent,
        camera_id: str | None = None,
        event_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Convert one SafetyEvent into a JSON-compatible
        canonical event record.
        """

        if not isinstance(event, SafetyEvent):
            raise TypeError(
                "event must be a SafetyEvent instance"
            )

        if event.frame_index < 0:
            raise ValueError(
                "frame_index cannot be negative"
            )

        if event.timestamp_ms < 0:
            raise ValueError(
                "timestamp_ms cannot be negative"
            )

        if not 0.0 <= event.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if event.persistence_frames < 0:
            raise ValueError(
                "persistence_frames cannot be negative"
            )

        if metadata is None:
            metadata = {}

        if event_id is None:
            event_id = self._generate_event_id(
                event=event,
                camera_id=camera_id,
            )

        return {
            "schema_version": self.SCHEMA_VERSION,

            "event_id": event_id,

            "camera_id": camera_id,

            "frame_index": int(
                event.frame_index
            ),

            "timestamp_ms": int(
                event.timestamp_ms
            ),

            "event_type": str(
                event.event_type
            ),

            "severity": str(
                event.severity
            ),

            "confidence": round(
                float(event.confidence),
                4,
            ),

            "track_ids": [
                int(event.track_id)
            ],

            "zone_id": event.zone_id,

            "persistence_frames": int(
                event.persistence_frames
            ),

            "movement": self._clean_value(
                event.movement
            ),

            "zone_transition": self._clean_value(
                event.zone_transition
            ),

            "metadata": self._clean_value(
                metadata
            ),
        }

    def to_json(
        self,
        event: dict[str, Any],
    ) -> str:
        """
        Convert a canonical event dictionary
        into formatted JSON.
        """

        if not isinstance(event, dict):
            raise TypeError(
                "event must be a dictionary"
            )

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
        """
        Save a canonical event as a JSON file.
        """

        if not isinstance(event, dict):
            raise TypeError(
                "event must be a dictionary"
            )

        event_id = event.get("event_id")

        if not event_id:
            raise ValueError(
                "event must contain event_id"
            )

        if filename is None:
            filename = f"{event_id}.json"

        output_path = (
            self.output_dir / filename
        )

        with output_path.open(
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
        event: SafetyEvent,
        camera_id: str | None,
    ) -> str:
        """
        Generate a deterministic event identifier.

        CAM_NONE is used when no camera ID is available.
        """

        camera_part = (
            camera_id
            if camera_id is not None
            else "CAM_NONE"
        )

        return (
            f"EVT_"
            f"{camera_part}_"
            f"{event.frame_index}_"
            f"{event.track_id}_"
            f"{event.event_type}"
        )

    @staticmethod
    def _clean_value(
        value: Any,
    ) -> Any:
        """
        Convert common Python structures into
        JSON-safe structures.

        Tuples become lists and nested structures
        are recursively cleaned.
        """

        if isinstance(value, dict):

            return {
                str(key): EventOutput._clean_value(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):

            return [
                EventOutput._clean_value(item)
                for item in value
            ]

        if isinstance(value, float):

            return round(
                value,
                4,
            )

        return value