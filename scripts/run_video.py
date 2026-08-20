"""Run the Member 1 detector on one video and save annotated output + JSON Lines results."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.detection import PersonObjectDetector


def draw_detections(frame, result: dict) -> None:
    """Draw DetectionResult v1 detections in place."""
    height, width = frame.shape[:2]
    scale = max(0.35, min(0.9, min(width, height) / 720))
    line_thickness = max(1, round(2 * scale))
    text_thickness = max(1, round(2 * scale))
    padding = max(3, round(5 * scale))

    for detection in result["detections"]:
        x1, y1, x2, y2 = detection["bbox_xyxy"]
        label = f'{detection["class_name"]} {detection["confidence"]:.0%}'
        (label_width, label_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, scale, text_thickness
        )
        label_top = max(0, y1 - label_height - baseline - 2 * padding)
        label_right = min(width, x1 + label_width + 2 * padding)
        cv2.rectangle(frame, (x1, label_top), (label_right, y1), (0, 130, 0), cv2.FILLED)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), line_thickness)
        cv2.putText(
            frame,
            label,
            (x1 + padding, y1 - padding - baseline),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            (255, 255, 255),
            text_thickness,
            cv2.LINE_AA,
        )

    count_label = f'People: {result["people_count"]}'
    (count_width, count_height), count_baseline = cv2.getTextSize(
        count_label, cv2.FONT_HERSHEY_SIMPLEX, scale, text_thickness
    )
    cv2.rectangle(
        frame,
        (padding, padding),
        (count_width + 3 * padding, count_height + count_baseline + 3 * padding),
        (25, 25, 25),
        cv2.FILLED,
    )
    cv2.putText(
        frame,
        count_label,
        (2 * padding, count_height + 2 * padding),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (0, 230, 255),
        text_thickness,
        cv2.LINE_AA,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to an MP4 video file.")
    parser.add_argument("--output", type=Path, default=Path("outputs/annotated_output.mp4"),
                        help="Path to write the annotated output MP4.")
    parser.add_argument("--camera-id", default="CAM_01",
                        help="Camera ID string passed to detector (default: CAM_01).")
    parser.add_argument("--jsonl", type=Path, default=None,
                        help="Path to write JSON Lines results (default: based on output video path).")
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    # Validate input file exists
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Determine JSONL output path (default based on output video path)
    if args.jsonl is not None:
        jsonl_path = args.jsonl
    else:
        jsonl_path = output_path.with_suffix(".jsonl")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize detector
    detector = PersonObjectDetector()

    # Open video capture
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        print(f"Error: Cannot open video file: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps is None:
        fps = 30.0  # reasonable default

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    if not out.isOpened():
        print(f"Error: Could not create VideoWriter for: {output_path}", file=sys.stderr)
        cap.release()
        sys.exit(1)

    # Open JSONL file for writing
    jsonl_file = open(jsonl_path, "w", encoding="utf-8")

    frame_index = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # end of video or read error

        # Run detection
        result = detector.detect_frame(
            frame,
            camera_id=args.camera_id,
            frame_index=frame_index,
            timestamp_ms=int((frame_index / fps) * 1000) if fps > 0 else 0,
        )

        # Draw detections on frame
        annotated = frame.copy()
        draw_detections(annotated, result)

        # Write annotated frame
        out.write(annotated)

        # Write JSONL result for this frame
        jsonl_file.write(json.dumps(result, indent=2) + "\n")

        frame_index += 1

    # Cleanup
    cap.release()
    out.release()
    jsonl_file.close()
    cv2.destroyAllWindows()

    print(f"Annotated video: {output_path}")
    print(f"Detection results: {jsonl_path}")
    print(f"Total frames processed: {frame_index}")


if __name__ == "__main__":
    main()