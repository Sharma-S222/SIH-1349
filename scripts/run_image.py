"""Run the Member 1 detector on one image and save evidence for Phase 3."""

from __future__ import annotations

import argparse
import json
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
    parser.add_argument("--image", required=True, type=Path, help="Path to a JPG/PNG image.")
    parser.add_argument("--camera-id", default="CAM_01")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/image_tests"))
    args = parser.parse_args()

    frame = cv2.imread(str(args.image))
    if frame is None:
        raise FileNotFoundError(f"Could not read image: {args.image}")

    detector = PersonObjectDetector()
    result = detector.detect_frame(frame, camera_id=args.camera_id)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.image.stem
    annotated = frame.copy()
    draw_detections(annotated, result)
    annotated_path = args.output_dir / f"{stem}_annotated.jpg"
    json_path = args.output_dir / f"{stem}_detection.json"
    cv2.imwrite(str(annotated_path), annotated)
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Annotated image: {annotated_path}")
    print(f"Detection JSON: {json_path}")
    print(f"People count: {result['people_count']}")


if __name__ == "__main__":
    main()
