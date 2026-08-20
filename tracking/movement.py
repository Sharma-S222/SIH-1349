from dataclasses import dataclass
from math import atan2, degrees, sqrt

from state import TrackState


@dataclass
class MovementState:
    """
    Derived movement information for one tracked object.

    This class describes movement only.
    It does not decide whether the movement is dangerous,
    suspicious, or a violation.
    """

    track_id: int

    displacement: float
    total_distance: float

    direction_degrees: float
    direction: str

    speed_pixels_per_frame: float

    stationary: bool

    trajectory: list[tuple[float, float]]

    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "displacement": self.displacement,
            "total_distance": self.total_distance,
            "direction_degrees": self.direction_degrees,
            "direction": self.direction,
            "speed_pixels_per_frame": (
                self.speed_pixels_per_frame
            ),
            "stationary": self.stationary,
            "trajectory": [
                list(point)
                for point in self.trajectory
            ],
        }


class MovementAnalyzer:
    """
    Calculates movement from TrackState position history.

    The analyzer intentionally does not generate events.

    Example:

        TrackState
            ↓
        MovementAnalyzer
            ↓
        MovementState
            ↓
        Event/Safety logic
    """

    def __init__(
        self,
        stationary_threshold: float = 2.0,
        analysis_window: int = 5,
    ):
        if stationary_threshold < 0:
            raise ValueError(
                "stationary_threshold cannot be negative"
            )

        if analysis_window < 2:
            raise ValueError(
                "analysis_window must be at least 2"
            )

        self.stationary_threshold = (
            stationary_threshold
        )

        self.analysis_window = analysis_window

    def analyze(
        self,
        state: TrackState,
    ) -> MovementState:

        history = list(state.foot_history)

        # -------------------------------------------------
        # Not enough history
        # -------------------------------------------------

        if len(history) < 2:

            return MovementState(
                track_id=state.track_id,
                displacement=0.0,
                total_distance=0.0,
                direction_degrees=0.0,
                direction="stationary",
                speed_pixels_per_frame=0.0,
                stationary=True,
                trajectory=history,
            )

        # -------------------------------------------------
        # Use only the most recent analysis window.
        # -------------------------------------------------

        recent_history = history[
            -self.analysis_window:
        ]

        previous = recent_history[0]
        current = recent_history[-1]

        dx = current[0] - previous[0]
        dy = current[1] - previous[1]

        # -------------------------------------------------
        # Net displacement
        # -------------------------------------------------

        displacement = sqrt(
            dx * dx
            + dy * dy
        )

        # -------------------------------------------------
        # Total travelled distance
        # -------------------------------------------------

        total_distance = 0.0

        for i in range(1, len(recent_history)):

            x1, y1 = recent_history[i - 1]
            x2, y2 = recent_history[i]

            segment_distance = sqrt(
                (x2 - x1) ** 2
                + (y2 - y1) ** 2
            )

            total_distance += segment_distance

        # -------------------------------------------------
        # Direction
        # -------------------------------------------------

        if displacement > 0.0:

            direction_degrees = degrees(
                atan2(
                    dy,
                    dx,
                )
            )

        else:
            direction_degrees = 0.0

        direction = self._direction_name(
            dx,
            dy,
            displacement,
        )

        # -------------------------------------------------
        # Average speed over the analyzed frames
        # -------------------------------------------------

        frame_span = len(recent_history) - 1

        if frame_span > 0:
            speed = (
                total_distance
                / frame_span
            )
        else:
            speed = 0.0

        # -------------------------------------------------
        # Stationary classification
        # -------------------------------------------------

        stationary = (
            speed < self.stationary_threshold
        )

        return MovementState(
            track_id=state.track_id,
            displacement=round(
                displacement,
                2,
            ),
            total_distance=round(
                total_distance,
                2,
            ),
            direction_degrees=round(
                direction_degrees,
                2,
            ),
            direction=direction,
            speed_pixels_per_frame=round(
                speed,
                2,
            ),
            stationary=stationary,
            trajectory=recent_history,
        )

    @staticmethod
    def _direction_name(
        dx: float,
        dy: float,
        displacement: float,
    ) -> str:
        """
        Convert movement vector into a coarse direction.

        Image coordinates are used:

            right = +X
            down  = +Y
        """

        if displacement <= 0.0:
            return "stationary"

        angle = degrees(
            atan2(
                dy,
                dx,
            )
        )

        if -22.5 <= angle < 22.5:
            return "right"

        if 22.5 <= angle < 67.5:
            return "down-right"

        if 67.5 <= angle < 112.5:
            return "down"

        if 112.5 <= angle < 157.5:
            return "down-left"

        if (
            angle >= 157.5
            or angle < -157.5
        ):
            return "left"

        if -157.5 <= angle < -112.5:
            return "up-left"

        if -112.5 <= angle < -67.5:
            return "up"

        return "up-right"