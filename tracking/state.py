from dataclasses import dataclass, field
from typing import Any

from tracker import Track


@dataclass
class TrackState:
    track_id: int
    detection_id: int
    class_id: int
    class_name: str

    confidence: float
    bbox_xyxy: list[float]

    center: tuple[float, float]
    foot_point: tuple[float, float]

    first_seen_frame: int
    last_seen_frame: int

    # Number of frames in which this track has been observed
    frame_count: int = 1

    # Recent position history
    history: list[tuple[float, float]] = field(
        default_factory=list
    )

    # Recent foot-point history
    foot_history: list[tuple[float, float]] = field(
        default_factory=list
    )

    # Current zone assigned by the zone engine
    current_zone: str | None = None

    # Previous zone, useful for detecting entry/exit
    previous_zone: str | None = None

    def update(
        self,
        track: Track,
        frame_index: int,
        max_history: int = 30,
    ):
        self.detection_id = track.detection_id
        self.class_id = track.class_id
        self.class_name = track.class_name

        self.confidence = track.confidence
        self.bbox_xyxy = track.bbox_xyxy

        self.center = track.center
        self.foot_point = track.foot_point

        self.last_seen_frame = frame_index
        self.frame_count += 1

        self.history.append(track.center)
        self.foot_history.append(track.foot_point)

        # Keep only the most recent positions.
        if len(self.history) > max_history:
            self.history.pop(0)

        if len(self.foot_history) > max_history:
            self.foot_history.pop(0)

    def set_zone(self, zone_id: str | None):
        self.previous_zone = self.current_zone
        self.current_zone = zone_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "detection_id": self.detection_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox_xyxy": self.bbox_xyxy,
            "center": self.center,
            "foot_point": self.foot_point,
            "first_seen_frame": self.first_seen_frame,
            "last_seen_frame": self.last_seen_frame,
            "frame_count": self.frame_count,
            "history": self.history,
            "foot_history": self.foot_history,
            "current_zone": self.current_zone,
            "previous_zone": self.previous_zone,
        }


class TrackStateManager:

    def __init__(
        self,
        max_history: int = 30,
        max_missing_frames: int = 30,
    ):
        self.max_history = max_history
        self.max_missing_frames = max_missing_frames

        self.states: dict[int, TrackState] = {}

    def update(
        self,
        tracks: list[Track],
        frame_index: int,
    ) -> list[TrackState]:

        active_ids = set()

        for track in tracks:

            track_id = track.track_id
            active_ids.add(track_id)

            # --------------------------------
            # New track
            # --------------------------------

            if track_id not in self.states:

                state = TrackState(
                    track_id=track_id,
                    detection_id=track.detection_id,
                    class_id=track.class_id,
                    class_name=track.class_name,
                    confidence=track.confidence,
                    bbox_xyxy=track.bbox_xyxy,
                    center=track.center,
                    foot_point=track.foot_point,
                    first_seen_frame=frame_index,
                    last_seen_frame=frame_index,
                    frame_count=1,
                    history=[track.center],
                    foot_history=[track.foot_point],
                )

                self.states[track_id] = state

            # --------------------------------
            # Existing track
            # --------------------------------

            else:

                self.states[track_id].update(
                    track,
                    frame_index,
                    self.max_history,
                )

        # --------------------------------
        # Remove tracks missing for too long
        # --------------------------------

        expired_ids = []

        for track_id, state in self.states.items():

            if track_id in active_ids:
                continue

            missing_frames = (
                frame_index - state.last_seen_frame
            )

            if missing_frames > self.max_missing_frames:
                expired_ids.append(track_id)

        for track_id in expired_ids:
            del self.states[track_id]

        # --------------------------------
        # Return currently active states
        # --------------------------------

        return [
            self.states[track_id]
            for track_id in active_ids
            if track_id in self.states
        ]

    def get(self, track_id: int) -> TrackState | None:
        return self.states.get(track_id)

    def remove(self, track_id: int):
        self.states.pop(track_id, None)

    def reset(self):
        self.states.clear()