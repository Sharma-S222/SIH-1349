import json
from pathlib import Path

from adapter import adapt_detections
from tracker import TrackerWrapper
from state import TrackStateManager
from movement import MovementAnalyzer
from zones import ZoneEngine
from events import EventEngine
from ouput import EventOutput


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("outputs/test_input")
OUTPUT_DIR = "outputs/events"


# ============================================================
# LOAD MEMBER 1 INPUT
# ============================================================

def load_frames():
    """
    Load synthetic Member 1 detection-v1 frames
    in chronological order.
    """

    files = sorted(
        INPUT_DIR.glob("frame_*.json")
    )

    for file_path in files:

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            yield json.load(file)


# ============================================================
# ERROR OUTPUT
# ============================================================

def print_error(error):
    """
    Print errors as structured JSON.
    """

    error_output = {
        "schema_version": "1.0",
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
# EVENT EXTRACTION
# ============================================================

def extract_event_fields(event):
    """
    Convert either an Event object or dictionary
    into the fields required by event-v1.
    """

    if isinstance(event, dict):

        return {
            "event_type": event.get(
                "event_type",
                "unknown",
            ),

            "severity": event.get(
                "severity",
                "INFO",
            ),

            "confidence": float(
                event.get(
                    "confidence",
                    0.0,
                )
            ),

            "track_ids": event.get(
                "track_ids",
                [],
            ),

            "zone_id": event.get(
                "zone_id"
            ),

            "persistence_ms": int(
                event.get(
                    "persistence_ms",
                    0,
                )
            ),

            "metadata": event.get(
                "metadata",
                {},
            ),

            "event_id": event.get(
                "event_id"
            ),
        }

    track_id = getattr(
        event,
        "track_id",
        None,
    )

    if track_id is None:
        track_ids = []
    else:
        track_ids = [track_id]

    return {
        "event_type": getattr(
            event,
            "event_type",
            "unknown",
        ),

        "severity": getattr(
            event,
            "severity",
            "INFO",
        ),

        "confidence": float(
            getattr(
                event,
                "confidence",
                0.0,
            )
        ),

        "track_ids": track_ids,

        "zone_id": getattr(
            event,
            "zone_id",
            None,
        ),

        "persistence_ms": int(
            getattr(
                event,
                "persistence_ms",
                0,
            )
        ),

        "metadata": getattr(
            event,
            "metadata",
            {},
        ),

        "event_id": getattr(
            event,
            "event_id",
            None,
        ),
    }


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    try:

        # ----------------------------------------------------
        # Load frames
        # ----------------------------------------------------

        frames = load_frames()

        # ----------------------------------------------------
        # Initialize pipeline ONCE
        #
        # These objects must persist across frames.
        # ----------------------------------------------------

        tracker = TrackerWrapper()

        state_manager = TrackStateManager(
            max_history=30,
            max_missing_frames=30,
        )

        movement_analyzer = MovementAnalyzer(
            stationary_threshold=2.0,
        )

        # ----------------------------------------------------
        # Restricted zone
        #
        # Replace these coordinates with the actual
        # restricted-zone polygon.
        # ----------------------------------------------------

        zones = [
            {
                "zone_id": "TRACK_RESTRICTED",

                "polygon": [
                    (300, 700),
                    (800, 700),
                    (800, 1080),
                    (300, 1080),
                ],
            }
        ]

        zone_engine = ZoneEngine(
            zones=zones
        )

        # ----------------------------------------------------
        # Event engine
        # ----------------------------------------------------

        event_engine = EventEngine(
            intrusion_min_frames=3,
        )

        # ----------------------------------------------------
        # Final output
        # ----------------------------------------------------

        event_output = EventOutput(
            output_dir=OUTPUT_DIR
        )

        # ----------------------------------------------------
        # Process every Member 1 frame
        # ----------------------------------------------------

        for data in frames:

            camera_id = data.get(
                "camera_id"
            )

            # ================================================
            # MEMBER 1 → ADAPTER
            # ================================================

            detections = adapt_detections(
                data
            )

            # ================================================
            # ADAPTER → TRACKER
            # ================================================

            tracks = tracker.update(
                detections
            )

            # ================================================
            # TRACKER → STATE
            # ================================================

            states = state_manager.update(
                tracks,
                frame_index=data[
                    "frame_index"
                ],
            )

            # ================================================
            # STATE → MOVEMENT
            # ================================================

            movements = {}

            for state in states:

                movements[
                    state.track_id
                ] = movement_analyzer.analyze(
                    state
                )

            # ================================================
            # STATE → ZONE
            # ================================================

            transitions = {}

            for state in states:

                transitions[
                    state.track_id
                ] = zone_engine.update(
                    track_id=state.track_id,
                    point=state.foot_point,
                )

            # ================================================
            # EVENT ENGINE
            # ================================================

            for state in states:

                movement = movements.get(
                    state.track_id
                )

                transition = transitions.get(
                    state.track_id
                )

                if movement is None:
                    continue

                if transition is None:
                    continue

                events = event_engine.process(
                    state=state,
                    movement=movement,
                    transition=transition,
                    frame_index=data[
                        "frame_index"
                    ],
                    timestamp_ms=data[
                        "timestamp_ms"
                    ],
                )

                if events is None:
                    continue

                # Support one event or a list
                if not isinstance(
                    events,
                    list,
                ):
                    events = [events]

                # ============================================
                # EVENT → EVENT-V1
                # ============================================

                for event in events:

                    fields = extract_event_fields(
                        event
                    )

                    payload = (
                        event_output.build_event(
                            event_type=fields[
                                "event_type"
                            ],

                            camera_id=camera_id,

                            timestamp_ms=data[
                                "timestamp_ms"
                            ],

                            track_ids=fields[
                                "track_ids"
                            ],

                            zone_id=fields[
                                "zone_id"
                            ],

                            confidence=fields[
                                "confidence"
                            ],

                            severity=fields[
                                "severity"
                            ],

                            persistence_ms=fields[
                                "persistence_ms"
                            ],

                            metadata=fields[
                                "metadata"
                            ],

                            event_id=fields[
                                "event_id"
                            ],
                        )
                    )

                    # ========================================
                    # ONLY SUCCESS OUTPUT
                    # ========================================

                    print(
                        event_output.to_json(
                            payload
                        )
                    )

                    # ========================================
                    # SAVE EVENT
                    # ========================================

                    event_output.save(
                        payload
                    )

    except Exception as error:

        # ================================================
        # ONLY ERROR OUTPUT
        # ================================================

        print_error(error)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()