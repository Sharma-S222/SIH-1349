import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tracking"))

from tracking.state import TrackState
from tracking.movement import MovementState
from tracking.zones import ZoneTransition
from tracking.events import EventEngine, SafetyEvent


def _make_state(track_id=1, confidence=0.9):
    return TrackState(
        track_id=track_id,
        detection_id="det_0_0",
        class_id=0,
        class_name="person",
        confidence=confidence,
        bbox_xyxy=[100.0, 200.0, 300.0, 400.0],
        center=(200.0, 300.0),
        foot_point=(200.0, 400.0),
        first_seen_frame=0,
        last_seen_frame=0,
        frame_count=1,
        history=[(200.0, 300.0)],
        foot_history=[(200.0, 400.0)],
    )


def _make_movement(track_id=1):
    return MovementState(
        track_id=track_id,
        displacement=10.0,
        total_distance=15.0,
        direction_degrees=90.0,
        direction="down",
        speed_pixels_per_frame=5.0,
        stationary=False,
        trajectory=[(200.0, 300.0), (200.0, 305.0)],
    )


def test_zone_entry_event():
    engine = EventEngine(intrusion_min_frames=3)
    state = _make_state()
    movement = _make_movement()
    transition = ZoneTransition(
        track_id=1, previous_zone=None, current_zone="ZONE_A",
        entered=True, exited=False, changed=True,
    )
    events = engine.process(state, movement, transition, frame_index=0, timestamp_ms=0, camera_id="CAM_0")
    assert len(events) == 1
    assert events[0].event_type == "zone_entry"


def test_zone_exit_event():
    engine = EventEngine(intrusion_min_frames=3)
    state = _make_state()
    movement = _make_movement()
    transition = ZoneTransition(
        track_id=1, previous_zone="ZONE_A", current_zone=None,
        entered=False, exited=True, changed=True,
    )
    events = engine.process(state, movement, transition, frame_index=0, timestamp_ms=0, camera_id="CAM_0")
    assert len(events) == 1
    assert events[0].event_type == "zone_exit"


def test_restricted_zone_intrusion():
    engine = EventEngine(intrusion_min_frames=3)
    state = _make_state()
    movement = _make_movement()
    transition = ZoneTransition(
        track_id=1, previous_zone=None, current_zone="TRACK_RESTRICTED",
        entered=True, exited=False, changed=True,
    )
    all_events = engine.process(state, movement, transition, frame_index=0, timestamp_ms=0, camera_id="CAM_0")
    assert len(all_events) == 1
    assert all_events[0].event_type == "zone_entry"

    for i in range(1, 5):
        transition2 = ZoneTransition(
            track_id=1, previous_zone="TRACK_RESTRICTED", current_zone="TRACK_RESTRICTED",
            entered=False, exited=False, changed=False,
        )
        frame_events = engine.process(state, movement, transition2, frame_index=i, timestamp_ms=i * 100, camera_id="CAM_0")
        all_events.extend(frame_events)

    intrusion_events = [e for e in all_events if e.event_type == "restricted_zone_intrusion"]
    assert len(intrusion_events) == 1
    assert intrusion_events[0].severity == "HIGH"


def test_camera_scoped_event_state():
    engine = EventEngine(intrusion_min_frames=3)
    state1 = _make_state(track_id=1)
    state2 = _make_state(track_id=1)
    movement = _make_movement()

    transition_cam0 = ZoneTransition(
        track_id=1, previous_zone=None, current_zone="TRACK_RESTRICTED",
        entered=True, exited=False, changed=True,
    )
    engine.process(state1, movement, transition_cam0, frame_index=0, timestamp_ms=0, camera_id="CAM_0")

    transition_cam1 = ZoneTransition(
        track_id=1, previous_zone=None, current_zone="TRACK_RESTRICTED",
        entered=True, exited=False, changed=True,
    )
    events_cam1 = engine.process(state2, movement, transition_cam1, frame_index=0, timestamp_ms=0, camera_id="CAM_1")
    assert len(events_cam1) == 1
    assert events_cam1[0].event_type == "zone_entry"

