import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tracking"))

from tracking.adapter import adapt_detections
from tracking.state import TrackStateManager
from tracking.movement import MovementAnalyzer
from tracking.zones import Zone, ZoneEngine
from tracking.events import EventEngine
from tracking.output import EventOutput


def _make_frame(detections=None, frame_index=0, timestamp_ms=0, camera_id="CAM_0"):
    if detections is None:
        detections = []
    return {
        "schema_version": "detection-v1",
        "camera_id": camera_id,
        "frame_index": frame_index,
        "timestamp_ms": timestamp_ms,
        "frame_width": 810,
        "frame_height": 1080,
        "people_count": len(detections),
        "detections": detections,
    }


def _make_detection(detection_id="det_0_0", bbox=None):
    if bbox is None:
        bbox = [100.0, 200.0, 300.0, 400.0]
    return {
        "detection_id": detection_id,
        "class_id": 0,
        "class_name": "person",
        "confidence": 0.9,
        "bbox_xyxy": bbox,
    }


def test_adapter_to_output_pipeline():
    frame = _make_frame(detections=[_make_detection()])
    detections = adapt_detections(frame)
    assert len(detections) == 1
    assert detections[0].detection_id == "det_0_0"

    state_mgr = TrackStateManager(max_history=30, max_missing_frames=30)
    analyzer = MovementAnalyzer()
    zones = ZoneEngine(zones=[
        Zone(zone_id="TRACK_RESTRICTED", name="Restricted",
             polygon=[(50.0, 50.0), (500.0, 50.0), (500.0, 500.0), (50.0, 500.0)])
    ])
    event_engine = EventEngine(intrusion_min_frames=3)
    output = EventOutput()

    assert output.SCHEMA_VERSION == "event-v1"
    assert detections[0].bbox_xyxy == [100.0, 200.0, 300.0, 400.0]
    assert state_mgr.states == {}

