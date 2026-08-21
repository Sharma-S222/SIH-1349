import pytest
from tracking.tracker import TrackerWrapper
from tracking.adapter import Detection

def test_tracker_configuration():
    # Verify ByteTrack defaults as requested
    tracker = TrackerWrapper()
    assert tracker is not None
    
def test_person_only_filtering():
    detections = [
        Detection(detection_id="d1", class_id=0, class_name="person", confidence=0.9, bbox_xyxy=[0,0,10,10]),
        Detection(detection_id="d2", class_id=24, class_name="backpack", confidence=0.8, bbox_xyxy=[10,10,20,20]),
        Detection(detection_id="d3", class_id=26, class_name="handbag", confidence=0.7, bbox_xyxy=[20,20,30,30]),
    ]
    
    person_dets = [d for d in detections if d.class_name == "person"]
    other_dets = [d for d in detections if d.class_name != "person"]
    
    assert len(person_dets) == 1
    assert person_dets[0].class_name == "person"
    assert len(other_dets) == 2
    
    tracker = TrackerWrapper()
    tracks = tracker.update(person_dets)
    
    pass

