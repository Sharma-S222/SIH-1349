import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tracking"))

from tracking.zones import Zone, ZoneEngine, ZoneTransition


def _make_zone(zone_id="ZONE_A", polygon=None):
    if polygon is None:
        polygon = [(100.0, 100.0), (500.0, 100.0), (500.0, 500.0), (100.0, 500.0)]
    return Zone(zone_id=zone_id, name=f"Zone {zone_id}", polygon=polygon)


def test_point_inside_zone():
    zone = _make_zone()
    engine = ZoneEngine(zones=[zone])
    result = engine.get_zone((200.0, 200.0))
    assert result == "ZONE_A"


def test_point_outside_zone():
    zone = _make_zone()
    engine = ZoneEngine(zones=[zone])
    result = engine.get_zone((600.0, 600.0))
    assert result is None


def test_zone_transition_entered():
    zone = _make_zone()
    engine = ZoneEngine(zones=[zone])
    transition = engine.update(track_id=1, point=(200.0, 200.0), previous_zone=None)
    assert transition.entered is True
    assert transition.exited is False
    assert transition.changed is True


def test_zone_transition_exited():
    zone = _make_zone()
    engine = ZoneEngine(zones=[zone])
    transition = engine.update(track_id=1, point=(600.0, 600.0), previous_zone="ZONE_A")
    assert transition.exited is True
    assert transition.entered is False
    assert transition.changed is True


def test_zone_transition_same_zone():
    zone = _make_zone()
    engine = ZoneEngine(zones=[zone])
    transition = engine.update(track_id=1, point=(200.0, 200.0), previous_zone="ZONE_A")
    assert transition.entered is False
    assert transition.exited is False
    assert transition.changed is False

