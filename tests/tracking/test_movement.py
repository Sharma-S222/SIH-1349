import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tracking"))

from tracking.state import TrackState
from tracking.movement import MovementAnalyzer


def _make_state(track_id=1, foot_history=None):
    if foot_history is None:
        foot_history = [(100.0, 200.0)]
    return TrackState(
        track_id=track_id,
        detection_id="det_0_0",
        class_id=0,
        class_name="person",
        confidence=0.9,
        bbox_xyxy=[100.0, 200.0, 300.0, 400.0],
        center=(200.0, 300.0),
        foot_point=(200.0, 400.0),
        first_seen_frame=0,
        last_seen_frame=0,
        frame_count=1,
        history=[(200.0, 300.0)],
        foot_history=foot_history,
    )


def test_stationary_when_no_history():
    state = _make_state(foot_history=[])
    analyzer = MovementAnalyzer()
    movement = analyzer.analyze(state)
    assert movement.stationary is True
    assert movement.speed_pixels_per_frame == 0.0


def test_stationary_when_single_point():
    state = _make_state(foot_history=[(100.0, 200.0)])
    analyzer = MovementAnalyzer()
    movement = analyzer.analyze(state)
    assert movement.stationary is True


def test_moving_detected():
    history = [(0.0, 0.0), (0.0, 10.0), (0.0, 20.0), (0.0, 30.0), (0.0, 40.0)]
    state = _make_state(foot_history=history)
    analyzer = MovementAnalyzer(stationary_threshold=2.0, analysis_window=5)
    movement = analyzer.analyze(state)
    assert movement.stationary is False
    assert movement.speed_pixels_per_frame > 0


def test_direction_calculation():
    history = [(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)]
    state = _make_state(foot_history=history)
    analyzer = MovementAnalyzer(stationary_threshold=2.0, analysis_window=5)
    movement = analyzer.analyze(state)
    assert movement.direction == "right"


def test_direction_down():
    history = [(0.0, 0.0), (0.0, 10.0), (0.0, 20.0)]
    state = _make_state(foot_history=history)
    analyzer = MovementAnalyzer(stationary_threshold=2.0, analysis_window=5)
    movement = analyzer.analyze(state)
    assert movement.direction == "down"


def test_total_distance_vs_displacement():
    history = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    state = _make_state(foot_history=history)
    analyzer = MovementAnalyzer(stationary_threshold=2.0, analysis_window=5)
    movement = analyzer.analyze(state)
    assert movement.total_distance > movement.displacement

