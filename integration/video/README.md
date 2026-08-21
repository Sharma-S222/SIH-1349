# Video Runtime — Member 5

Video source abstraction and camera manager for SIH1349.

## Architecture

```
CameraManager
    ├── CAM_PLATFORM_01
    │     ├── VideoSource (File/RTSP/Webcam)
    │     ├── bounded queue (size=3)
    │     └── CameraState
    └── CAM_ENTRY_01 (future)
```

**MVP:** ONE ACTIVE CAMERA (`CAM_PLATFORM_01`).

## Sources

| Source | Class | Notes |
|--------|-------|-------|
| File | `FileVideoSource` | Local MP4/AVI |
| Webcam | `WebcamVideoSource` | Configurable device index |
| RTSP | `RTSPVideoSource` | Reconnect, credential sanitization |

## Frame Contract

```python
@dataclass
class Frame:
    camera_id: str       # e.g. "CAM_PLATFORM_01"
    frame_index: int     # monotonically increasing per camera
    timestamp_ms: float  # milliseconds
    frame: np.ndarray    # uint8, HxWx3, BGR
    width: int
    height: int
    source_type: str     # "file" | "webcam" | "rtsp"
```

## Usage

```python
from integration.video import CameraManager, load_camera_config

configs = load_camera_config("integration/configs/cameras.example.yaml")
manager = CameraManager(configs)
manager.start_all()

frame = manager.get_frame("CAM_PLATFORM_01", timeout=2.0)
# frame.frame is a BGR numpy array

manager.stop_all()
```

## Configuration

See `integration/configs/cameras.example.yaml`.

## Identity Rule

Future tracking must scope identity as `(camera_id, track_id)`.
Never assume `track_id` is globally unique across cameras.
