from dataclasses import dataclass
from math import atan2, degrees, sqrt

from state import TrackState


@dataclass
class MovementState:
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
            "speed_pixels_per_frame": self.speed_pixels_per_frame,
            "stationary": self.stationary,
            "trajectory": self.trajectory,
        }


class MovementAnalyzer:

    def __init__(
        self,
        stationary_threshold: float = 2.0,
        analysis_window: int = 5,
    ):
        self.stationary_threshold = float(
            stationary_threshold
        )

        self.analysis_window = max(
            2,
            int(analysis_window),
        )

    def analyze(
        self,
        state: TrackState,
    ) -> MovementState:

        history = list(
            state.foot_history
        )

        # ----------------------------------------------------
        # No movement history
        # ----------------------------------------------------

        if not history:

            return self._stationary_state(
                state,
                [],
            )

        # ----------------------------------------------------
        # Use only the most recent positions
        # ----------------------------------------------------

        history = history[
            -self.analysis_window:
        ]

        if len(history) < 2:

            return self._stationary_state(
                state,
                history,
            )

        # ----------------------------------------------------
        # Start and current positions
        # ----------------------------------------------------

        start_x, start_y = history[0]
        current_x, current_y = history[-1]

        dx = current_x - start_x
        dy = current_y - start_y

        displacement = sqrt(
            dx * dx
            + dy * dy
        )

        # ----------------------------------------------------
        # Total travelled distance
        #
        # This is different from displacement.
        #
        # Displacement:
        #     start → current
        #
        # Total distance:
        #     sum of every movement segment
        # ----------------------------------------------------

        total_distance = 0.0

        for i in range(1, len(history)):

            previous_x, previous_y = (
                history[i - 1]
            )

            next_x, next_y = history[i]

            segment_distance = sqrt(
                (next_x - previous_x) ** 2
                + (next_y - previous_y) ** 2
            )

            total_distance += segment_distance

        # ----------------------------------------------------
        # Average speed
        # ----------------------------------------------------

        frame_intervals = len(history) - 1

        speed = (
            total_distance / frame_intervals
            if frame_intervals > 0
            else 0.0
        )

        # ----------------------------------------------------
        # Stationary detection
        #
        # Use average movement rather than one noisy frame.
        # ----------------------------------------------------

        stationary = (
            speed < self.stationary_threshold
        )

        # ----------------------------------------------------
        # Direction
        # ----------------------------------------------------

        if displacement <= self.stationary_threshold:

            direction_degrees = 0.0
            direction = "stationary"

        else:

            direction_degrees = degrees(
                atan2(
                    dy,
                    dx,
                )
            )

            direction = self._direction_name(
                direction_degrees
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

            trajectory=history.copy(),
        )

    def _stationary_state(
        self,
        state: TrackState,
        history: list[tuple[float, float]],
    ) -> MovementState:

        return MovementState(
            track_id=state.track_id,
            displacement=0.0,
            total_distance=0.0,
            direction_degrees=0.0,
            direction="stationary",
            speed_pixels_per_frame=0.0,
            stationary=True,
            trajectory=history.copy(),
        )

    @staticmethod
    def _direction_name(
        angle: float,
    ) -> str:

        if -22.5 <= angle < 22.5:
            return "right"

        if 22.5 <= angle < 67.5:
            return "down-right"

        if 67.5 <= angle < 112.5:
            return "down"

        if 112.5 <= angle < 157.5:
            return "down-left"

        if angle >= 157.5 or angle < -157.5:
            return "left"

        if -157.5 <= angle < -112.5:
            return "up-left"

        if -112.5 <= angle < -67.5:
            return "up"

        return "up-right"