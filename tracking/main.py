import json
from pathlib import Path
from typing import Any

from adapter import adapt_detections
from tracker import TrackerWrapper
from state import TrackStateManager
from movement import MovementAnalyzer
from zones import Zone, ZoneEngine
from events import EventEngine
from ouput import EventOutput


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("outputs/test_input")
OUTPUT_DIR = "outputs/events"

CAMERA_ID = None


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
    Print errors as structured JSON.
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
    Create configured safety zones.

    Replace the polygon with the actual track
    restricted-area coordinates later.
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
# MAIN PIPELINE
# ============================================================

def main():

    try:

        # ----------------------------------------------------
        # Load Member 1 frames
        # ----------------------------------------------------

        frames = load_frames()

        # ----------------------------------------------------
        # Initialize pipeline ONCE
        #
        # These objects maintain information across frames.
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
        # Process every Member 1 frame
        # ----------------------------------------------------

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
            # MEMBER 1 → ADAPTER
            # =================================================

            detections = adapt_detections(
                data
            )

            # =================================================
            # ADAPTER → TRACKER
            # =================================================

            tracks = tracker.update(
                detections
            )

            # =================================================
            # TRACKER → STATE
            # =================================================

            states = state_manager.update(
                tracks,
                frame_index=frame_index,
            )

            # =================================================
            # PROCESS STATES
            # =================================================

            for state in states:

                # ---------------------------------------------
                # STATE → MOVEMENT
                # ---------------------------------------------

                movement = (
                    movement_analyzer.analyze(
                        state
                    )
                )

                # ---------------------------------------------
                # STATE → ZONE
                # ---------------------------------------------

                transition = (
                    zone_engine.update(
                        track_id=state.track_id,
                        point=state.foot_point,
                    )
                )

                # Keep state synchronized with
                # the zone engine.

                state.set_zone(
                    transition.current_zone
                )

                # ---------------------------------------------
                # MOVEMENT + ZONE + STATE
                # → EVENT ENGINE
                # ---------------------------------------------

                events = event_engine.process(
                    state=state,
                    movement=movement,
                    transition=transition,
                    frame_index=frame_index,
                    timestamp_ms=timestamp_ms,
                )

                if not events:
                    continue

                # ---------------------------------------------
                # EVENT → FINAL JSON
                # ---------------------------------------------

                for event in events:

                    payload = (
                        event_output.build_event(
                            event=event,
                            camera_id=CAMERA_ID,
                        )
                    )

                    # -----------------------------------------
                    # PRINT RAW JSON
                    # -----------------------------------------

                    print(
                        event_output.to_json(
                            payload
                        )
                    )

                    # -----------------------------------------
                    # SAVE JSON
                    # -----------------------------------------

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