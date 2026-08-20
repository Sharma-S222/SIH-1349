from dataclasses import dataclass
from typing import Any

import numpy as np
import supervision as sv

from trackers import ByteTrackTracker

from adapter import Detection


@dataclass
class Track:
    track_id: int
    detection_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: list[float]
    center: tuple[float, float]
    foot_point: tuple[float, float]
    confirmed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "detection_id": self.detection_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox_xyxy": self.bbox_xyxy,
            "center": self.center,
            "foot_point": self.foot_point,
            "confirmed": self.confirmed,
        }


class TrackerWrapper:

    def __init__(
        self,
        track_activation_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        minimum_iou_threshold: float = 0.8,
        minimum_consecutive_frames: int = 1,
        frame_rate: int = 30,
    ):

        self.tracker = ByteTrackTracker(
            track_activation_threshold=track_activation_threshold,
            lost_track_buffer=lost_track_buffer,
            minimum_iou_threshold=minimum_iou_threshold,
            minimum_consecutive_frames=minimum_consecutive_frames,
            frame_rate=frame_rate,
        )

    def update(
        self,
        detections: list[Detection],
    ) -> list[Track]:

        if not detections:
            return []

        xyxy = np.array(
            [d.bbox_xyxy for d in detections],
            dtype=np.float32,
        )

        confidence = np.array(
            [d.confidence for d in detections],
            dtype=np.float32,
        )

        class_id = np.array(
            [d.class_id for d in detections],
            dtype=int,
        )

        sv_detections = sv.Detections(
            xyxy=xyxy,
            confidence=confidence,
            class_id=class_id,
        )

        tracked = self.tracker.update(
            sv_detections
        )

        results = []

        if tracked.tracker_id is None:
            return results

        for i in range(len(tracked)):

            track_id = tracked.tracker_id[i]

            # ByteTrack can temporarily return -1
            # for an unconfirmed track.
            if track_id is None or track_id < 0:
                continue

            bbox = tracked.xyxy[i].tolist()

            if tracked.confidence is not None:
                confidence_value = float(
                    tracked.confidence[i]
                )
            else:
                confidence_value = 0.0

            if tracked.class_id is not None:
                class_value = int(
                    tracked.class_id[i]
                )
            else:
                class_value = 0

            x1, y1, x2, y2 = bbox

            center = (
                (x1 + x2) / 2.0,
                (y1 + y2) / 2.0,
            )

            foot_point = (
                (x1 + x2) / 2.0,
                y2,
            )

            # Match the current tracker result to
            # the closest original detection.
            detection_id = -1
            class_name = "unknown"

            if detections:

                best_index = 0
                best_distance = float("inf")

                tracked_center = center

                for j, detection in enumerate(
                    detections
                ):

                    dx = (
                        detection.bbox_xyxy[0]
                        + detection.bbox_xyxy[2]
                    ) / 2.0

                    dy = (
                        detection.bbox_xyxy[1]
                        + detection.bbox_xyxy[3]
                    ) / 2.0

                    distance = (
                        (dx - tracked_center[0]) ** 2
                        +
                        (dy - tracked_center[1]) ** 2
                    )

                    if distance < best_distance:
                        best_distance = distance
                        best_index = j

                detection_id = detections[
                    best_index
                ].detection_id

                class_name = detections[
                    best_index
                ].class_name

            results.append(
                Track(
                    track_id=int(track_id),
                    detection_id=detection_id,
                    class_id=class_value,
                    class_name=class_name,
                    confidence=confidence_value,
                    bbox_xyxy=bbox,
                    center=center,
                    foot_point=foot_point,
                    confirmed=True,
                )
            )

        return results

    def reset(self):
        self.tracker.reset()