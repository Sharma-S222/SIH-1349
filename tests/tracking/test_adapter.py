import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tracking"))

from tracking.adapter import adapt_detections, Detection


def _make_frame(detections=None, frame_index=0, timestamp_ms=0):
    if detections is None:
        detections = []
    return {
        "schema_version": "detection-v1",
        "camera_id": "CAM_0",
        "frame_index": frame_index,
        "timestamp_ms": timestamp_ms,
        "frame_width": 810,
        "frame_height": 1080,
        "people_count": len(detections),
        "detections": detections,
    }


def _make_detection(detection_id="det_0_0", class_id=0, class_name="person", confidence=0.9, bbox=None):
    if bbox is None:
        bbox = [100.0, 200.0, 300.0, 400.0]
    return {
        "detection_id": detection_id,
        "class_id": class_id,
        "class_name": class_name,
        "confidence": confidence,
        "bbox_xyxy": bbox,
    }


def test_detection_id_stays_string():
    frame = _make_frame(detections=[_make_detection()])
    result = adapt_detections(frame)
    assert len(result) == 1
    assert isinstance(result[0].detection_id, str)
    assert result[0].detection_id == "det_0_0"


def test_detection_id_not_converted_to_int():
    frame = _make_frame(detections=[_make_detection(detection_id="det_120_5")])
    result = adapt_detections(frame)
    det = result[0]
    assert isinstance(det.detection_id, str)
    assert det.detection_id == "det_120_5"


def test_multiple_detections_preserve_ids():
    dets = [_make_detection(detection_id=f"det_0_{i}") for i in range(5)]
    frame = _make_frame(detections=dets)
    result = adapt_detections(frame)
    assert [d.detection_id for d in result] == [f"det_0_{i}" for i in range(5)]


def test_schema_version_validation():
    frame = _make_frame()
    frame["schema_version"] = "detection-v2"
    try:
        adapt_detections(frame)
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_detection_bbox_parsing():
    bbox = [50.0, 100.0, 250.0, 350.0]
    frame = _make_frame(detections=[_make_detection(bbox=bbox)])
    result = adapt_detections(frame)
    det = result[0]
    assert det.bbox_xyxy == bbox
    assert det.width == 200.0
    assert det.height == 250.0
    assert det.center == (150.0, 225.0)
    assert det.foot_point == (150.0, 350.0)

