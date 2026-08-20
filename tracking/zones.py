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
        Ray-casting point-in-polygon test.
        """

        x, y = point
        inside = False

        n = len(self.polygon)

        if n < 3:
            return False

        j = n - 1

        for i in range(n):

            xi, yi = self.polygon[i]
            xj, yj = self.polygon[j]

            intersects = (
                (yi > y) != (yj > y)
                and
                x
                < (xj - xi)
                * (y - yi)
                / ((yj - yi) or 1e-12)
                + xi
            )

            if intersects:
                inside = not inside

            j = i

        return inside


@dataclass
class ZoneTransition:
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

    def __init__(
        self,
        zones: list[Zone] | None = None,
    ):
        self.zones = zones or []

        self.track_zones: dict[
            int,
            str | None,
        ] = {}

    def get_zone(
        self,
        point: tuple[float, float],
    ) -> str | None:

        for zone in self.zones:

            if zone.contains(point):
                return zone.zone_id

        return None

    def update(
        self,
        track_id: int,
        point: tuple[float, float],
    ) -> ZoneTransition:

        previous_zone = self.track_zones.get(
            track_id
        )

        current_zone = self.get_zone(
            point
        )

        entered = (
            current_zone is not None
            and current_zone != previous_zone
        )

        exited = (
            previous_zone is not None
            and current_zone != previous_zone
        )

        changed = (
            current_zone != previous_zone
        )

        self.track_zones[track_id] = (
            current_zone
        )

        return ZoneTransition(
            track_id=track_id,
            previous_zone=previous_zone,
            current_zone=current_zone,
            entered=entered,
            exited=exited,
            changed=changed,
        )

    def reset_track(
        self,
        track_id: int,
    ):
        self.track_zones.pop(
            track_id,
            None,
        )

    def reset(self):
        self.track_zones.clear()