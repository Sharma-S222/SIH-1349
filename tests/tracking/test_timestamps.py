import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tracking"))

from tracking.events import SafetyEvent
from tracking.output import EventOutput


def test_frame_timestamp_vs_epoch_timestamp():
    output = EventOutput()
    frame_timestamp_ms = 4000
    epoch_ms = int(time.time() * 1000)

    event = SafetyEvent(
        event_type="zone_entry",
        severity="INFO",
        confidence=0.9,
        track_id=1,
        zone_id="ZONE_A",
        frame_index=10,
        timestamp_ms=frame_timestamp_ms,
        persistence_frames=1,
        movement={},
        zone_transition={},
    )

    payload = output.build_event(event=event, camera_id="CAM_0", epoch_ms=epoch_ms)

    assert payload["timestamp"] == epoch_ms
    assert payload["metadata"]["source_timestamp_ms"] == frame_timestamp_ms
    assert payload["timestamp"] != payload["metadata"]["source_timestamp_ms"]

