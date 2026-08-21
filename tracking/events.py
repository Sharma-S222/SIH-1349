from dataclasses import dataclass
from typing import Any

from tracking.state import TrackState
from tracking.movement import MovementState
from tracking.zones import ZoneTransition


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
            "confidence": round(
                float(self.confidence),
                4,
            ),
            "track_id": self.track_id,
            "zone_id": self.zone_id,
            "frame_index": self.frame_index,
            "timestamp_ms": self.timestamp_ms,
            "persistence_frames": self.persistence_frames,
            "movement": self.movement,
            "zone_transition": self.zone_transition,
        }


class EventEngine:
    """
    Converts tracking, state, movement, and zone information
    into discrete safety events.

    This class does not perform detection or tracking.
    It only interprets already-refined data.

    All internal state is keyed by (camera_id, track_id, zone_id)
    to prevent cross-camera event leakage.
    """

    def __init__(
        self,
        intrusion_min_frames: int = 3,
    ):
        if intrusion_min_frames < 1:
            raise ValueError(
                "intrusion_min_frames must be at least 1"
            )

        self.intrusion_min_frames = (
            intrusion_min_frames
        )

        # Tracks which objects have already generated
        # a zone-entry event for a particular zone.
        self.zone_entry_events: set[
            tuple[str | None, int, str]
        ] = set()

        # Number of consecutive frames an object has
        # remained inside a restricted zone.
        self.restricted_zone_frames: dict[
            tuple[str | None, int, str],
            int,
        ] = {}

        # Prevent repeated intrusion events while the
        # same track remains continuously inside the zone.
        self.active_intrusions: set[
            tuple[str | None, int, str]
        ] = set()

    def process(
        self,
        state: TrackState,
        movement: MovementState,
        transition: ZoneTransition,
        frame_index: int,
        timestamp_ms: int,
        camera_id: str | None = None,
    ) -> list[SafetyEvent]:

        events: list[SafetyEvent] = []

        track_id = state.track_id
        current_zone = transition.current_zone
        previous_zone = transition.previous_zone

        # =================================================
        # ZONE ENTRY
        # =================================================

        if transition.entered:

            if current_zone is not None:

                event_key = (
                    camera_id,
                    track_id,
                    current_zone,
                )

                if (
                    event_key
                    not in self.zone_entry_events
                ):

                    self.zone_entry_events.add(
                        event_key
                    )

                    events.append(
                        SafetyEvent(
                            event_type="zone_entry",
                            severity="INFO",
                            confidence=state.confidence,
                            track_id=track_id,
                            zone_id=current_zone,
                            frame_index=frame_index,
                            timestamp_ms=timestamp_ms,
                            persistence_frames=1,
                            movement=movement.to_dict(),
                            zone_transition=(
                                transition.to_dict()
                            ),
                        )
                    )

        # =================================================
        # ZONE EXIT
        # =================================================

        if transition.exited:

            if previous_zone is not None:

                event_key = (
                    camera_id,
                    track_id,
                    previous_zone,
                )

                self.zone_entry_events.discard(
                    event_key
                )

                # Clear any restricted-zone state
                # when the object leaves the zone.
                self.restricted_zone_frames.pop(
                    event_key,
                    None,
                )

                self.active_intrusions.discard(
                    event_key
                )

                events.append(
                    SafetyEvent(
                        event_type="zone_exit",
                        severity="INFO",
                        confidence=state.confidence,
                        track_id=track_id,
                        zone_id=previous_zone,
                        frame_index=frame_index,
                        timestamp_ms=timestamp_ms,
                        persistence_frames=1,
                        movement=movement.to_dict(),
                        zone_transition=(
                            transition.to_dict()
                        ),
                    )
                )

        # =================================================
        # RESTRICTED ZONE INTRUSION
        # =================================================

        if current_zone == "TRACK_RESTRICTED":

            event_key = (
                camera_id,
                track_id,
                current_zone,
            )

            current_persistence = (
                self.restricted_zone_frames.get(
                    event_key,
                    0,
                )
                + 1
            )

            self.restricted_zone_frames[
                event_key
            ] = current_persistence

            # Generate exactly one intrusion event
            # after the required persistence threshold.
            if (
                current_persistence
                >= self.intrusion_min_frames
                and event_key
                not in self.active_intrusions
            ):

                self.active_intrusions.add(
                    event_key
                )

                events.append(
                    SafetyEvent(
                        event_type=(
                            "restricted_zone_intrusion"
                        ),
                        severity="HIGH",
                        confidence=state.confidence,
                        track_id=track_id,
                        zone_id=current_zone,
                        frame_index=frame_index,
                        timestamp_ms=timestamp_ms,
                        persistence_frames=(
                            current_persistence
                        ),
                        movement=movement.to_dict(),
                        zone_transition=(
                            transition.to_dict()
                        ),
                    )
                )

        else:
            # Object is not currently in the restricted
            # zone, so its persistence counter is irrelevant.
            for key in list(
                self.restricted_zone_frames
            ):
                if key[1] == track_id and key[0] == camera_id:
                    self.restricted_zone_frames.pop(
                        key,
                        None,
                    )

            for key in list(
                self.active_intrusions
            ):
                if key[1] == track_id and key[0] == camera_id:
                    self.active_intrusions.discard(
                        key
                    )

        return events

    def reset_track(
        self,
        track_id: int,
        camera_id: str | None = None,
    ) -> None:
        """
        Remove all event state associated with a track.
        """

        self.zone_entry_events = {
            key
            for key in self.zone_entry_events
            if key[1] != track_id or key[0] != camera_id
        }

        self.restricted_zone_frames = {
            key: value
            for key, value
            in self.restricted_zone_frames.items()
            if key[1] != track_id or key[0] != camera_id
        }

        self.active_intrusions = {
            key
            for key in self.active_intrusions
            if key[1] != track_id or key[0] != camera_id
        }

    def reset(self) -> None:
        """
        Reset all event state.
        """

        self.zone_entry_events.clear()
        self.restricted_zone_frames.clear()
        self.active_intrusions.clear()
