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
    ):
        self.stationary_threshold = stationary_threshold

    def analyze(
        self,
        state: TrackState,
    ) -> MovementState:

        history = state.foot_history

        # Not enough history to calculate movement.
        if len(history) < 2:

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

        # --------------------------------
        # Current and previous positions
        # --------------------------------

        previous = history[-2]
        current = history[-1]

        dx = current[0] - previous[0]
        dy = current[1] - previous[1]

        displacement = sqrt(
            dx * dx + dy * dy
        )

        # --------------------------------
        # Total travelled distance
        # --------------------------------

        total_distance = 0.0

        for i in range(1, len(history)):

            x1, y1 = history[i - 1]
            x2, y2 = history[i]

            segment = sqrt(
                (x2 - x1) ** 2
                + (y2 - y1) ** 2
            )

            total_distance += segment

        # --------------------------------
        # Direction
        # --------------------------------

        direction_degrees = (
            degrees(
                atan2(
                    dy,
                    dx,
                )
            )
            if displacement > 0
            else 0.0
        )

        direction = self._direction_name(
            dx,
            dy,
            displacement,
        )

        # --------------------------------
        # Speed
        # --------------------------------

        speed = displacement

        stationary = (
            speed < self.stationary_threshold
        )

        return MovementState(
            track_id=state.track_id,
            displacement=round(displacement, 2),
            total_distance=round(total_distance, 2),
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

    @staticmethod
    def _direction_name(
        dx: float,
        dy: float,
        displacement: float,
    ) -> str:

        if displacement == 0:
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

        if angle >= 157.5 or angle < -157.5:
            return "left"

        if -157.5 <= angle < -112.5:
            return "up-left"

        if -112.5 <= angle < -67.5:
            return "up"

        return "up-right"