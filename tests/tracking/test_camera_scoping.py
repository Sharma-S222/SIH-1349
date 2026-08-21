import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tracking"))

from tracking.state import TrackStateManager
from tracking.events import EventEngine
from tracking.zones import ZoneTransition
from tracking.movement import MovementState
from tracking.state import TrackState


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


def test_same_track_id_different_cameras_independent():
    mgr = TrackStateManager(max_history=30, max_missing_frames=30)

    from tracking.tracker import Track
    track1 = Track(track_id=1, detection_id="det_0_0", class_id=0, class_name="person",
                   confidence=0.9, bbox_xyxy=[10.0, 20.0, 50.0, 60.0],
                   center=(30.0, 40.0), foot_point=(30.0, 60.0))
    track2 = Track(track_id=1, detection_id="det_1_0", class_id=0, class_name="person",
                   confidence=0.8, bbox_xyxy=[100.0, 200.0, 300.0, 400.0],
                   center=(200.0, 300.0), foot_point=(200.0, 400.0))

    mgr.update([track1], frame_index=0, camera_id="CAM_0")
    mgr.update([track2], frame_index=0, camera_id="CAM_1")

    s0 = mgr.get(track_id=1, camera_id="CAM_0")
    s1 = mgr.get(track_id=1, camera_id="CAM_1")

    assert s0 is not s1
    assert s0.bbox_xyxy != s1.bbox_xyxy


def test_event_engine_camera_scoping():
    engine = EventEngine(intrusion_min_frames=3)
    state = _make_state()
    movement = _make_movement()

    t0 = ZoneTransition(track_id=1, previous_zone=None, current_zone="TRACK_RESTRICTED",
                        entered=True, exited=False, changed=True)
    engine.process(state, movement, t0, frame_index=0, timestamp_ms=0, camera_id="CAM_0")

    t1 = ZoneTransition(track_id=1, previous_zone=None, current_zone="TRACK_RESTRICTED",
                        entered=True, exited=False, changed=True)
    events1 = engine.process(state, movement, t1, frame_index=0, timestamp_ms=0, camera_id="CAM_1")

    assert len(events1) == 1
    assert events1[0].event_type == "zone_entry"

