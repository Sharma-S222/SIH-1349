import json
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import cv2
import requests

from integration.video.sources import FileVideoSource, WebcamVideoSource
from ai.detection.config import DetectorConfig
from ai.detection.detector import PersonObjectDetector
from tracking.adapter import adapt_detections
from tracking.tracker import TrackerWrapper
from tracking.state import TrackStateManager
from tracking.movement import MovementAnalyzer
from tracking.zones import Zone, ZoneEngine
from tracking.events import EventEngine
from tracking.output import EventOutput
import threading

logger = logging.getLogger(__name__)

class VideoPipeline:
    def __init__(
        self,
        video_path: Optional[str] = None,
        device_index: Optional[int] = None,
        camera_id: str = "CAM_PLATFORM_01",
        backend_url: Optional[str] = None,
        zone_config_path: Optional[str] = None,
        display: bool = False,
        output_path: Optional[str] = None,
    ):
        self.video_path = video_path
        self.camera_id = camera_id
        self.backend_url = backend_url
        self.display = display
        self.output_path = output_path
        
        if device_index is not None:
            self.source = WebcamVideoSource(camera_id, device_index=device_index)
        elif video_path:
            self.source = FileVideoSource(camera_id, video_path)
        else:
            raise ValueError("Must provide either video_path or device_index")
            
        if not self.source.open():
            raise RuntimeError(f"Failed to open video source")
            
        source_fps = 30
        if self.source._cap is not None:
            fps = self.source._cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                source_fps = int(round(fps))

        self.config = DetectorConfig()
        self.detector = PersonObjectDetector(self.config)
        
        self.tracker = TrackerWrapper(
            minimum_iou_threshold=0.1,
            minimum_consecutive_frames=2,
            frame_rate=source_fps
        )
        self.state_mgr = TrackStateManager()
        self.movement = MovementAnalyzer()
        
        zones = []
        if zone_config_path and Path(zone_config_path).exists():
            with open(zone_config_path, "r") as f:
                data = json.load(f)
                for z in data.get("zones", []):
                    zones.append(Zone(
                        zone_id=z["zone_id"],
                        name=z["name"],
                        polygon=[(float(p[0]), float(p[1])) for p in z["polygon"]]
                    ))
        self.zones = ZoneEngine(zones=zones)
        self.events = EventEngine(intrusion_min_frames=3)
        self.output = EventOutput()
        
        self.frames_processed = 0
        self.total_inference_time = 0.0
        self.events_generated = 0
        self.person_detections = 0
        self.other_detections = 0
        self.last_stream_time = 0.0
        
        self.out_writer = None
        if self.output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            width = int(self.source._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.source._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if width == 0 or height == 0:
                width, height = 1280, 720
            scale = min(1280 / width, 720 / height) if width > 0 else 1.0
            if scale > 1.0: scale = 1.0
            out_width = int(width * scale)
            out_height = int(height * scale)
            self.out_writer = cv2.VideoWriter(self.output_path, fourcc, source_fps, (out_width, out_height))

    def run(self):
        start_time = time.time()
        logger.info("Pipeline starting...")
        
        try:
            while True:
                frame = self.source.read()
                if frame is None:
                    break
                    
                inf_start = time.time()
                det_result = self.detector.detect_frame(
                    frame.frame,
                    camera_id=frame.camera_id,
                    frame_index=frame.frame_index,
                    timestamp_ms=frame.timestamp_ms
                )
                inf_elapsed = time.time() - inf_start
                self.total_inference_time += inf_elapsed
                
                adapted_dets = adapt_detections(det_result)
                
                person_dets = [d for d in adapted_dets if d.class_name == "person"]
                self.person_detections += len(person_dets)
                other_dets = [d for d in adapted_dets if d.class_name != "person"]
                self.other_detections += len(other_dets)
                
                tracks = self.tracker.update(person_dets)
                states = self.state_mgr.update(tracks, frame_index=frame.frame_index, camera_id=frame.camera_id)
                
                for s in states:
                    mov = self.movement.analyze(s)
                    transition = self.zones.update(s.track_id, s.foot_point)
                    s.set_zone(transition.current_zone)
                    evs = self.events.process(s, mov, transition, frame.frame_index, frame.timestamp_ms, frame.camera_id)
                    
                    for e in evs:
                        event_json = self.output.build_event(e, camera_id=frame.camera_id, epoch_ms=frame.timestamp_ms)
                        self.events_generated += 1
                        
                        if event_json["event_type"] == "restricted_zone_intrusion" and self.backend_url:
                            self._post_async(f"{self.backend_url}/api/events", json=event_json)
                
                self.frames_processed += 1
                
                display_frame = self._render_preview(frame.frame, person_dets, other_dets, states, inf_elapsed, start_time)
                
                if self.out_writer:
                    self.out_writer.write(display_frame)
                    
                if self.display:
                    cv2.imshow("Preview", display_frame)
                    key = cv2.waitKey(1)
                    if key == 27 or key == ord('q'):  # ESC or Q
                        break
                        
                # Handle backend streaming & telemetry (~10 fps)
                now = time.time()
                if self.backend_url and (now - self.last_stream_time) > 0.1:
                    self.last_stream_time = now
                    self._stream_to_backend(display_frame, person_dets, other_dets, states, inf_elapsed, start_time)
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
        finally:
            self._cleanup(start_time)

    def _cleanup(self, start_time):
        elapsed = time.time() - start_time
        logger.info(f"Pipeline finished. Frames: {self.frames_processed}, Elapsed: {elapsed:.2f}s")
        if elapsed > 0:
            logger.info(f"Overall pipeline FPS: {self.frames_processed / elapsed:.2f}")
        logger.info(f"Total detections: {self.person_detections + self.other_detections}")
        logger.info(f"Person detections: {self.person_detections}")
        logger.info(f"Other-object detections: {self.other_detections}")
        logger.info(f"Events generated: {self.events_generated}")
        logger.info(f"Unique Person IDs: {len(self.state_mgr.states)}")

        if self.out_writer:
            self.out_writer.release()
        if self.source._cap:
            self.source._cap.release()
        if self.display:
            cv2.destroyAllWindows()

    def _post_async(self, url, json=None, data=None, headers=None):
        def _send():
            try:
                requests.post(url, json=json, data=data, headers=headers, timeout=1.0)
            except Exception as e:
                pass # Fire and forget
        threading.Thread(target=_send, daemon=True).start()

    def _stream_to_backend(self, display_frame, person_dets, other_dets, states, inf_elapsed, pipeline_start_time):
        elapsed = time.time() - pipeline_start_time
        fps = self.frames_processed / elapsed if elapsed > 0 else 0.0
        
        # JPEG Encode
        ret, buffer = cv2.imencode('.jpg', display_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if ret:
            self._post_async(f"{self.backend_url}/api/cameras/{self.camera_id}/frame", data=buffer.tobytes(), headers={'Content-Type': 'image/jpeg'})
            
        # Telemetry
        objects_dict = {}
        for d in other_dets:
            objects_dict[d.class_name] = objects_dict.get(d.class_name, 0) + 1
            
        telemetry = {
            "source_type": "LIVE_CAMERA" if isinstance(self.source, WebcamVideoSource) else "VIDEO",
            "status": "PROCESSING",
            "people_count": len(person_dets),
            "active_tracks": len(states),
            "unique_person_ids": len(self.state_mgr.states),
            "objects": objects_dict,
            "pipeline_fps": round(fps, 1),
            "inference_ms": round(inf_elapsed * 1000, 1),
        }
        self._post_async(f"{self.backend_url}/api/cameras/{self.camera_id}/telemetry", json=telemetry)

    def _render_preview(self, frame_bgr, person_dets, other_dets, states, inf_elapsed, pipeline_start_time):
        height, width = frame_bgr.shape[:2]
        scale = min(1280 / width, 720 / height)
        if scale > 1.0: scale = 1.0
        
        display_frame = cv2.resize(frame_bgr, (int(width * scale), int(height * scale)))
        
        for z in self.zones.zones:
            pts = [(int(p[0] * scale), int(p[1] * scale)) for p in z.polygon]
            pts_array = __import__("numpy").array(pts, __import__("numpy").int32)
            cv2.polylines(display_frame, [pts_array], isClosed=True, color=(0, 0, 255), thickness=2)
            cv2.putText(display_frame, z.name, (pts[0][0], max(0, pts[0][1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        state_map = {s.track_id: s for s in states}
        for s in states:
            x1, y1, x2, y2 = s.bbox_xyxy
            x1, y1, x2, y2 = int(x1 * scale), int(y1 * scale), int(x2 * scale), int(y2 * scale)
            color = (0, 255, 0)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            label = f"Person ID:{s.track_id} {int(s.confidence * 100)}%"
            cv2.putText(display_frame, label, (x1, max(0, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            fx, fy = int(s.foot_point[0] * scale), int(s.foot_point[1] * scale)
            cv2.circle(display_frame, (fx, fy), 4, color, -1)

        for d in other_dets:
            x1, y1, x2, y2 = d.bbox_xyxy
            x1, y1, x2, y2 = int(x1 * scale), int(y1 * scale), int(x2 * scale), int(y2 * scale)
            color = (255, 165, 0)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            label = f"{d.class_name} {int(d.confidence * 100)}%"
            cv2.putText(display_frame, label, (x1, max(0, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        elapsed = time.time() - pipeline_start_time
        fps = self.frames_processed / elapsed if elapsed > 0 else 0.0
        info = [
            f"{self.camera_id} - LIVE",
            f"Pipeline FPS: {fps:.1f}",
            f"Inference: {inf_elapsed * 1000:.1f}ms",
            f"Active Person Tracks: {len(states)}",
            f"People Detected: {len(person_dets)}",
            f"Other Objects: {len(other_dets)}",
            f"Unique Person IDs: {len(self.state_mgr.states)}",
        ]
        
        y0 = 30
        for text in info:
            cv2.putText(display_frame, text, (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display_frame, text, (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            y0 += 25
            
        return display_frame
