from dataclasses import dataclass
from typing import Any

from state import TrackState
from movement import MovementState
from zones import ZoneTransition


@dataclass
class SafetyEvent:
    event_type: str
    severity: str
    confidence: float

    track_id: int
    zone_id: str | None

    frame_index: int
    timestamp_ms: int

    persistence_frames: int

    movement: dict[str, Any]
    zone_transition: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "track_id": self.track_id,
            "zone_id": self.zone_id,
            "frame_index": self.frame_index,
            "timestamp_ms": self.timestamp_ms,
            "persistence_frames": self.persistence_frames,
            "movement": self.movement,
            "zone_transition": self.zone_transition,
        }


class EventEngine:

    def __init__(
        self,
        intrusion_min_frames: int = 3,
    ):
        self.intrusion_min_frames = (
            intrusion_min_frames
        )

        self.zone_entry_events: set[
            tuple[int, str]
        ] = set()

    def process(
        self,
        state: TrackState,
        movement: MovementState,
        transition: ZoneTransition,
        frame_index: int,
        timestamp_ms: int,
    ) -> list[SafetyEvent]:

        events = []

        # --------------------------------
        # Zone entry
        # --------------------------------

        if transition.entered:

            zone_id = transition.current_zone

            if zone_id is not None:

                event_key = (
                    state.track_id,
                    zone_id,
                )

                # Only generate one entry event
                # for this track entering this zone.
                if event_key not in self.zone_entry_events:

                    self.zone_entry_events.add(
                        event_key
                    )

                    events.append(
                        SafetyEvent(
                            event_type="zone_entry",
                            severity="INFO",
                            confidence=state.confidence,
                            track_id=state.track_id,
                            zone_id=zone_id,
                            frame_index=frame_index,
                            timestamp_ms=timestamp_ms,
                            persistence_frames=state.frame_count,
                            movement=movement.to_dict(),
                            zone_transition=transition.to_dict(),
                        )
                    )

        # --------------------------------
        # Zone exit
        # --------------------------------

        if transition.exited:

            zone_id = transition.previous_zone

            if zone_id is not None:

                self.zone_entry_events.discard(
                    (
                        state.track_id,
                        zone_id,
                    )
                )

                events.append(
                    SafetyEvent(
                        event_type="zone_exit",
                        severity="INFO",
                        confidence=state.confidence,
                        track_id=state.track_id,
                        zone_id=zone_id,
                        frame_index=frame_index,
                        timestamp_ms=timestamp_ms,
                        persistence_frames=state.frame_count,
                        movement=movement.to_dict(),
                        zone_transition=transition.to_dict(),
                    )
                )

        # --------------------------------
        # Restricted-zone intrusion
        # --------------------------------

        if (
            transition.current_zone
            == "TRACK_RESTRICTED"
        ):

            if (
                state.frame_count
                >= self.intrusion_min_frames
            ):

                events.append(
                    SafetyEvent(
                        event_type="restricted_zone_intrusion",
                        severity="HIGH",
                        confidence=state.confidence,
                        track_id=state.track_id,
                        zone_id=transition.current_zone,
                        frame_index=frame_index,
                        timestamp_ms=timestamp_ms,
                        persistence_frames=state.frame_count,
                        movement=movement.to_dict(),
                        zone_transition=transition.to_dict(),
                    )
                )

        return events

    def reset_track(
        self,
        track_id: int,
    ):
        self.zone_entry_events = {
            key
            for key in self.zone_entry_events
            if key[0] != track_id
        }

    def reset(self):
        self.zone_entry_events.clear()