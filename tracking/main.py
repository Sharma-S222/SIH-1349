import json
import time
from pathlib import Path
from typing import Any

from tracking.adapter import adapt_detections
from tracking.tracker import TrackerWrapper
from tracking.state import TrackStateManager
from tracking.movement import MovementAnalyzer
from tracking.zones import Zone, ZoneEngine
from tracking.events import EventEngine
from tracking.output import EventOutput


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("outputs/test_input")
OUTPUT_DIR = "outputs/events"

# Single-camera MVP.
# Replace with actual camera identity when available.
CAMERA_ID = "CAM_0"


# ============================================================
# LOAD MEMBER 1 INPUT
# ============================================================

def load_frames():
    """
    Load Member 1 detection JSON frames
    in chronological order.
    """

    files = sorted(
        INPUT_DIR.glob("frame_*.json")
    )

    for file_path in files:

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            yield json.load(file)


# ============================================================
# ERROR OUTPUT
# ============================================================

def print_error(error: Exception):
    """
    Print errors as JSON.
    """

    error_output = {
        "schema_version": "1.1",
        "status": "error",
        "error": {
            "type": type(error).__name__,
            "message": str(error),
        },
    }

    print(
        json.dumps(
            error_output,
            indent=2,
            ensure_ascii=False,
        )
    )


# ============================================================
# ZONE CONFIGURATION
# ============================================================

def create_zones() -> list[Zone]:
    """
    Create the configured safety zones.

    These coordinates are placeholders for testing.
    Replace them with the actual restricted-area polygon.
    """

    return [
        Zone(
            zone_id="TRACK_RESTRICTED",
            name="Track Restricted Area",
            polygon=[
                (300.0, 700.0),
                (800.0, 700.0),
                (800.0, 1080.0),
                (300.0, 1080.0),
            ],
        )
    ]


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        # ----------------------------------------------------
        # Initialize pipeline components ONCE
        # ----------------------------------------------------

        tracker = TrackerWrapper()

        state_manager = TrackStateManager(
            max_history=30,
            max_missing_frames=30,
        )

        movement_analyzer = MovementAnalyzer(
            stationary_threshold=2.0,
        )

        zone_engine = ZoneEngine(
            zones=create_zones()
        )

        event_engine = EventEngine(
            intrusion_min_frames=3,
        )

        event_output = EventOutput(
            output_dir=OUTPUT_DIR
        )

        # ----------------------------------------------------
        # Process Member 1 frames
        # ----------------------------------------------------

        frames = load_frames()

        for data in frames:

            frame_index = int(
                data.get(
                    "frame_index",
                    0,
                )
            )

            timestamp_ms = int(
                data.get(
                    "timestamp_ms",
                    0,
                )
            )

            # =================================================
            # MEMBER 1 â†’ ADAPTER
            # =================================================

            detections = adapt_detections(
                data
            )

            # =================================================
            # ADAPTER â†’ TRACKER
            # =================================================

            tracks = tracker.update(
                detections
            )

            # =================================================
            # TRACKER â†’ STATE
            # =================================================

            states = state_manager.update(
                tracks,
                frame_index=frame_index,
                camera_id=CAMERA_ID,
            )

            # =================================================
            # PROCESS EACH ACTIVE TRACK
            # =================================================

            for state in states:

                # ------------------------------------------------
                # STATE â†’ MOVEMENT
                # ------------------------------------------------

                movement = (
                    movement_analyzer.analyze(
                        state
                    )
                )

                # ------------------------------------------------
                # STATE â†’ ZONE
                # ------------------------------------------------

                transition = zone_engine.update(
                    track_id=state.track_id,
                    point=state.foot_point,
                )

                # Keep TrackState synchronized.
                state.set_zone(
                    transition.current_zone
                )

                # ------------------------------------------------
                # STATE + MOVEMENT + ZONE â†’ EVENTS
                # ------------------------------------------------

                events = event_engine.process(
                    state=state,
                    movement=movement,
                    transition=transition,
                    frame_index=frame_index,
                    timestamp_ms=timestamp_ms,
                    camera_id=CAMERA_ID,
                )

                # No event means there is nothing to send
                # to the event output layer.

                if not events:
                    continue

                # ------------------------------------------------
                # EVENT â†’ CANONICAL OUTPUT
                # ------------------------------------------------

                for event in events:

                    payload = (
                        event_output.build_event(
                            event=event,
                            camera_id=CAMERA_ID,
                            epoch_ms=int(time.time() * 1000),
                        )
                    )

                    # ------------------------------------------------
                    # RAW JSON OUTPUT
                    # ------------------------------------------------

                    print(
                        event_output.to_json(
                            payload
                        )
                    )

                    # ------------------------------------------------
                    # SAVE JSON
                    # ------------------------------------------------

                    event_output.save(
                        payload
                    )

    except Exception as error:

        print_error(error)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
