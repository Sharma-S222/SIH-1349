import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tracking"))

from tracking.state import TrackState, TrackStateManager
from tracking.tracker import Track


def _make_track(track_id=1, detection_id="det_0_0", class_id=0, class_name="person", confidence=0.9, bbox=None):
    if bbox is None:
        bbox = [100.0, 200.0, 300.0, 400.0]
    return Track(
        track_id=track_id,
        detection_id=detection_id,
        class_id=class_id,
        class_name=class_name,
        confidence=confidence,
        bbox_xyxy=bbox,
        center=(200.0, 300.0),
        foot_point=(200.0, 400.0),
        confirmed=True,
    )


def test_camera_scoped_state_keying():
    mgr = TrackStateManager(max_history=30, max_missing_frames=30)
    tracks_cam0 = [_make_track(track_id=1)]
    tracks_cam1 = [_make_track(track_id=1)]

    mgr.update(tracks_cam0, frame_index=0, camera_id="CAM_0")
    mgr.update(tracks_cam1, frame_index=0, camera_id="CAM_1")

    state0 = mgr.get(track_id=1, camera_id="CAM_0")
    state1 = mgr.get(track_id=1, camera_id="CAM_1")

    assert state0 is not None
    assert state1 is not None
    assert state0.track_id == state1.track_id == 1


def test_camera_scoped_state_independence():
    mgr = TrackStateManager(max_history=30, max_missing_frames=30)
    cam0_tracks = [_make_track(track_id=1, bbox=[10.0, 20.0, 50.0, 60.0])]
    cam1_tracks = [_make_track(track_id=1, bbox=[100.0, 200.0, 300.0, 400.0])]

    mgr.update(cam0_tracks, frame_index=0, camera_id="CAM_0")
    mgr.update(cam1_tracks, frame_index=0, camera_id="CAM_1")

    state0 = mgr.get(track_id=1, camera_id="CAM_0")
    state1 = mgr.get(track_id=1, camera_id="CAM_1")

    assert state0.bbox_xyxy != state1.bbox_xyxy


def test_state_manager_update_returns_active():
    mgr = TrackStateManager(max_history=30, max_missing_frames=30)
    tracks = [_make_track(track_id=1), _make_track(track_id=2)]
    result = mgr.update(tracks, frame_index=0, camera_id="CAM_0")
    assert len(result) == 2


def test_state_manager_removes_expired():
    mgr = TrackStateManager(max_history=30, max_missing_frames=2)
    tracks = [_make_track(track_id=1)]
    mgr.update(tracks, frame_index=0, camera_id="CAM_0")
    mgr.update([], frame_index=1, camera_id="CAM_0")
    mgr.update([], frame_index=2, camera_id="CAM_0")
    mgr.update([], frame_index=3, camera_id="CAM_0")

    state = mgr.get(track_id=1, camera_id="CAM_0")
    assert state is None


def test_state_history_capped():
    mgr = TrackStateManager(max_history=5, max_missing_frames=30)
    for i in range(10):
        tracks = [_make_track(track_id=1)]
        mgr.update(tracks, frame_index=i, camera_id="CAM_0")
    state = mgr.get(track_id=1, camera_id="CAM_0")
    assert len(state.history) <= 5
    assert len(state.foot_history) <= 5

