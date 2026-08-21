from dataclasses import dataclass
from typing import Any


@dataclass
class Zone:
    zone_id: str
    name: str
    polygon: list[tuple[float, float]]

    def contains(
        self,
        point: tuple[float, float],
    ) -> bool:
        """
        Determine whether a point lies inside the zone polygon.

        Uses the ray-casting algorithm.
        """

        if len(self.polygon) < 3:
            return False

        x, y = point
        inside = False

        j = len(self.polygon) - 1

        for i in range(len(self.polygon)):
            xi, yi = self.polygon[i]
            xj, yj = self.polygon[j]

            # Check whether the horizontal ray from the point
            # crosses this polygon edge.
            crosses = (
                (yi > y) != (yj > y)
            )

            if crosses:
                denominator = yj - yi

                if abs(denominator) > 1e-12:
                    intersection_x = (
                        (xj - xi)
                        * (y - yi)
                        / denominator
                        + xi
                    )

                    if x < intersection_x:
                        inside = not inside

            j = i

        return inside


@dataclass
class ZoneTransition:
    """
    Result of evaluating one tracked object's zone position.
    """

    track_id: int

    previous_zone: str | None
    current_zone: str | None

    entered: bool
    exited: bool
    changed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "previous_zone": self.previous_zone,
            "current_zone": self.current_zone,
            "entered": self.entered,
            "exited": self.exited,
            "changed": self.changed,
        }


class ZoneEngine:
    """
    Determines which configured zone contains a tracked
    object's reference point.

    The engine does not generate safety events or messages.
    It only produces zone information and transitions.
    """

    def __init__(
        self,
        zones: list[Zone] | None = None,
    ):
        self.zones = list(zones or [])

    def get_zone(
        self,
        point: tuple[float, float],
    ) -> str | None:
        """
        Return the zone containing the point.

        If the point is outside every configured zone,
        return None.

        If zones overlap, the first matching zone wins.
        """

        for zone in self.zones:
            if zone.contains(point):
                return zone.zone_id

        return None

    def update(
        self,
        track_id: int,
        point: tuple[float, float],
        previous_zone: str | None = None,
    ) -> ZoneTransition:
        """
        Evaluate the current zone for a tracked object.

        `previous_zone` should normally come from TrackState.
        This keeps TrackState as the source of truth rather
        than maintaining a second copy of the same state here.
        """

        current_zone = self.get_zone(point)

        # ---------------------------------------------
        # Zone transition semantics
        # ---------------------------------------------

        # Object was outside and is now inside.
        entered = (
            previous_zone is None
            and current_zone is not None
        )

        # Object was inside and is now outside.
        exited = (
            previous_zone is not None
            and current_zone is None
        )

        # Any actual zone change.
        changed = (
            previous_zone != current_zone
        )

        return ZoneTransition(
            track_id=track_id,
            previous_zone=previous_zone,
            current_zone=current_zone,
            entered=entered,
            exited=exited,
            changed=changed,
        )

    def update_state(
        self,
        state: Any,
    ) -> ZoneTransition:
        """
        Convenience method for directly processing a TrackState.

        The state object must provide:

            track_id
            foot_point
            current_zone
            set_zone()
        """

        transition = self.update(
            track_id=state.track_id,
            point=state.foot_point,
            previous_zone=state.current_zone,
        )

        state.set_zone(
            transition.current_zone
        )

        return transition

    def reset(self) -> None:
        """
        Kept for pipeline compatibility.

        ZoneEngine no longer owns persistent track-zone state,
        so there is nothing to clear here.
        """

        return None
