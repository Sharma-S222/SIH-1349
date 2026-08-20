# RT-DETRv2-S Person Detection - Member 1

This project implements a person detection system using the RT-DETRv2-S model for the SIH-1349 competition.

## Project Purpose

The system detects persons (and selected objects: backpack, handbag, suitcase) in images and video frames using the RT-DETRv2-S model. It outputs results in the DetectionResult v1 schema format, including people count, bounding boxes, class labels, and confidence scores.

## Requirements

### Python Version
Python 3.10+ recommended.

### Dependencies

Install via:

```bash
pip install -r requirements.txt
```

The following packages are required (verified by project imports):

- **torch** (2.13.0) - PyTorch framework
- **opencv-python** (5.0.0.93) - image processing and video I/O
- **numpy** (2.5.2) - array operations
- **jsonschema** (4.26.0) - schema validation
- **pytest** (9.1.1) - test framework

### Installation

1. Clone the repository
2. Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Model Setup

The project uses the **RT-DETRv2-S** model, version **baseline-v1**.

- **Model weights**: `weights/rtdetrv2_s.pth` (81MB, pretrained on COCO dataset)
- **Model config**: `third_party/RT-DETR/rtdetrv2_pytorch/configs/rtdetrv2/rtdetrv2_r18vd_120e_coco.yml`
- **How the detector finds the model**: The `DetectorConfig` class in `ai/detection/config.py` sets `weights_path` to `PROJECT_ROOT / "weights" / "rtdetrv2_s.pth"` and `model_root` to `PROJECT_ROOT / "third_party" / "RT-DETR" / "rtdetrv2_pytorch"`

**Important**: The model weight file must be placed at `weights/rtdetrv2_s.pth` relative to the project root. If the file is missing, the `PersonObjectDetector` will raise `FileNotFoundError`.

There is currently no automated download script. If the model weights are not present, obtain the RT-DETRv2-S baseline-v1 checkpoint pretrained on COCO and place it at `weights/rtdetrv2_s.pth`.

## Image Inference

Run detection on a single image:

```bash
.\.venv\Scripts\python.exe scripts\run_image.py --image <path_to_image> --camera-id CAM_01
```

**Example:**

```bash
.\.venv\Scripts\python.exe scripts\run_image.py --image sample_bus.jpg --camera-id CAM_01
```

**Output**:

- Annotated image: `outputs/image_tests/<image_name>_annotated.jpg`
- JSON detection result: `outputs/image_tests/<image_name>_detection.json`

**Example results** (sample_bus.jpg):

- People count: **4**
- Detection JSON includes `schema_version`, `camera_id`, `frame_index`, `timestamp_ms`, `frame_width`, `frame_height`, `people_count`, and `detections` list
- Each detection has: `detection_id`, `class_id`, `class_name`, `confidence`, `bbox_xyxy` `[x1, y1, x2, y2]`

## Video Inference

Run detection on a video file:

```bash
.\.venv\Scripts\python.exe scripts\run_video.py --input <path_to_mp4> --output <path_to_output_mp4> --camera-id CAM_01
```

**Example**:

```bash
.\.venv\Scripts\python.exe scripts\run_video.py --input test1.mp4 --output outputs/test1_output.mp4 --camera-id CAM_01
```

**Output**:

- Annotated MP4 video at the specified output path
- JSON Lines results at `outputs/test1_result.jsonl` (one DetectionResult v1 dict per line)
- FPS depends on frame count and hardware (see Known Limitations below)

## `detect_frame()` API

```python
from ai.detection.detector import PersonObjectDetector
from ai.detection.config import DetectorConfig

detector = PersonObjectDetector(DetectorConfig())
result = detector.detect_frame(
    frame,           # BGR NumPy array (height, width, 3)
    camera_id="CAM_01",  # optional, default "CAM_01"
    frame_index=0    # optional, default 0
)
```

**Returned DetectionResult v1 dict structure**:

```json
{
  "schema_version": "1.0",
  "camera_id": "CAM_01",
  "frame_index": 0,
  "timestamp_ms": 0,
  "frame_width": 640,
  "frame_height": 480,
  "people_count": 4,
  "detections": [
    {
      "detection_id": 1,
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.9534,
      "bbox_xyxy": [49, 399, 248, 905]
    },
    ...
  ],
  "inference_ms": 307.44,
  "model": {"name": "RT-DETRv2-S", "version": "baseline-v1"}
}
```

**Key points**:

- `track_id` is **NOT** included. Tracking IDs are owned by Member 2.
- Bounding boxes are in `[x1, y1, x2, y2]` format, clamped to frame dimensions.
- `people_count` = number of detections where `class_name == "person"`.
- `inference_ms` = time in milliseconds for the model forward pass.

## DetectionResult v1

The output schema (`detection_result_v1.json`) requires these top-level fields:

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | `string` | `"1.0"` |
| `camera_id` | `string` | Camera identifier, default `"CAM_01"` |
| `frame_index` | `integer` | Frame index, default `0` |
| `timestamp_ms` | `integer` | Timestamp in milliseconds, default `0` |
| `frame_width` | `integer` | Frame width in pixels |
| `frame_height` | `integer` | Frame height in pixels |
| `people_count` | `integer` | Count of person detections after filtering |
| `detections` | `array` | List of detection objects |

Each detection object:

| Field | Type | Description |
|---------|------|-------------|
| `detection_id` | `integer` | Local ID, 1-based, sequential within the frame |
| `class_id` | `integer` | COCO class ID (0 = person) |
| `class_name` | `string` | Class name (`person`, `backpack`, `handbag`, `suitcase`) |
| `confidence` | `float` | Detection confidence score (0.0 to 1.0) |
| `bbox_xyxy` | `array[int, int, int, int]` | `[x1, y1, x2, y2]` pixel coordinates, clamped to frame dimensions |

**`track_id` is NOT included.** Tracking IDs are owned by Member 2.

## People Counting

`people_count` is calculated as:

```python
people_count = sum(item["class_name"] == "person" for item in detections)
```

This counts only detections where `class_name` is `"person"`, after confidence thresholding (`>= 0.50`) and allowed-class filtering (`person`, `backpack`, `handbag`, `suitcase`).

**Example**: If a frame has 5 detections: 3 persons, 1 backpack, 1 car, then `people_count` = 3.

## Tests

Run the complete test suite:

```bash
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

**Current result**: 78 passed, 0 failed, 0 skipped

**Test file breakdown**:

- `tests/test_bounding_boxes.py` (10 tests)
- `tests/test_class_filtering.py` (9 tests)
- `tests/test_confidence.py` (10 tests)
- `tests/test_detection_result.py` (7 tests)
- `tests/test_detect_frame.py` (6 tests)
- `tests/test_empty_detections.py` (6 tests)
- `tests/test_people_counting.py` (6 tests)
- `tests/test_difficult_scenes.py` (4 tests)
- `tests/test_benchmarking.py` (5 tests)
- `tests/test_integration_mocked.py` (5 mocked integration tests)
- `tests/test_integration_real.py` (1 real-model integration test)
- `tests/test_integration_handoff.py` (8 integration/handoff tests)

## Known Limitations

The following are known limitations of the current implementation:

- **Small/occluded objects**: Very small persons or heavily occluded persons may not be detected.
- **Low-light CCTV**: Poor lighting reduces detection accuracy; the detector may miss persons or produce lower-confidence detections.
- **Camera angle limitations**: Significant perspective distortion (e.g., overhead views) can affect bounding box accuracy.
- **Crowded scenes**: Dense crowds can cause overlapping bounding boxes and missed detections.
- **Performance**: Inference time varies by hardware; on CPU, typical latency is 200-500 ms per frame. GPU acceleration is recommended for real-time FPS.
- **Model limitations**: RT-DETRv2-S is pretrained on COCO; classes beyond `person`, `backpack`, `handbag`, `suitcase` are filtered out by the `allowed_classes` configuration.
- **Input resolution**: Fixed input size of 640x640 may cause distortion for extreme aspect ratios.

## Reproducibility

A fresh developer should be able to:

1. **Clone** the repository
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Obtain the model**: Place `rtdetrv2_s.pth` at `weights/rtdetrv2_s.pth` (pretrained on COCO)
4. **Place the model correctly**: The detector expects `weights/rtdetrv2_s.pth` relative to the project root
5. **Run image inference**: `.\.venv\Scripts\python.exe scripts\run_image.py --image <image_path> --camera-id CAM_01`
6. **Run video inference**: `.\.venv\Scripts\python.exe scripts\run_video.py --input <mp4> --output <output_mp4> --camera-id CAM_01`
7. **Use `detect_frame()`**: Import `PersonObjectDetector` and `DetectorConfig` from `ai.detection`, then call `detect_frame(frame, camera_id, frame_index)`
8. **Run tests**: `.\.venv\Scripts\python.exe -m pytest tests/ -v`

**Verified**: 78/78 tests pass, image inference produces correct DetectionResult v1 JSON, people counting is accurate.