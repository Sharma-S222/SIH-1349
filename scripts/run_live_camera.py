import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integration.runtime.video_pipeline import VideoPipeline
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def parse_args():
    parser = argparse.ArgumentParser(description="SIH1349 Live Camera Pipeline")
    parser.add_argument("--device-index", type=int, default=None, help="Webcam device index (default: None)")
    parser.add_argument("--video-file", type=str, default=None, help="Path to video file")
    parser.add_argument("--loop", action="store_true", help="Loop the video file")
    parser.add_argument("--camera-id", required=True, help="Camera ID to simulate")
    parser.add_argument("--backend-url", help="URL of the backend API (e.g. http://127.0.0.1:8000)")
    parser.add_argument("--zone-config", help="Path to zone configuration JSON")
    parser.add_argument("--display", action="store_true", help="Show annotated preview window")
    parser.add_argument("--output", help="Path to save annotated MP4")
    parser.add_argument("--stream-fps", type=int, default=10, help="MJPEG stream target FPS")
    return parser.parse_args()

def main():
    args = parse_args()
    
    pipeline = VideoPipeline(
        device_index=args.device_index,
        video_path=args.video_file,
        camera_id=args.camera_id,
        backend_url=args.backend_url,
        zone_config_path=args.zone_config,
        display=args.display,
        output_path=args.output,
        loop=args.loop,
    )
    
    pipeline.run()

if __name__ == "__main__":
    main()
