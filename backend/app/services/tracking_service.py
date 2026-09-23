from pathlib import Path

from ultralytics import YOLO

from app.core.config import settings
from app.core.constants import PERSON_CLASS_ID


class TrackingService:
    """
    YOLOv8 + ByteTrack tracking service.

    The same YOLO model performs person detection and passes
    the detections to ByteTrack through Ultralytics' tracking API.

    IMPORTANT:
    Keep one TrackingService instance alive for an entire
    video/image sequence so ByteTrack can maintain identities
    across frames.
    """

    def __init__(
        self,
        model_path: str | None = None,
        confidence_threshold: float | None = None,
    ):
        self.model_path = model_path or settings.yolo_model_path

        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.detection_confidence
        )

        model_file = Path(self.model_path)

        if not model_file.exists():
            raise FileNotFoundError(
                f"YOLO model not found: {model_file}"
            )

        self.model = YOLO(str(model_file))

    def update(self, frame, frame_id: int) -> dict:
        """
        Process one frame and return ByteTrack results.

        Returns:
            {
                "frame_id": int,
                "tracks": [
                    {
                        "track_id": int,
                        "bbox": [x1, y1, x2, y2],
                        "confidence": float,
                        "class_id": int,
                        "center": [cx, cy]
                    }
                ]
            }
        """

        results = self.model.track(
            source=frame,
            conf=self.confidence_threshold,
            classes=[PERSON_CLASS_ID],
            tracker="bytetrack.yaml",
            persist=True,
            imgsz=1280,
            verbose=False,
        )
        if not results:
            return {
                "frame_id": frame_id,
                "tracks": [],
            }

        result = results[0]

        if result.boxes is None:
            return {
                "frame_id": frame_id,
                "tracks": [],
            }

        # ByteTrack IDs are not available until tracks are established.
        if result.boxes.id is None:
            return {
                "frame_id": frame_id,
                "tracks": [],
            }

        boxes = result.boxes.xyxy.cpu().tolist()
        confidences = result.boxes.conf.cpu().tolist()
        class_ids = result.boxes.cls.int().cpu().tolist()
        track_ids = result.boxes.id.int().cpu().tolist()

        tracks = []

        for bbox, confidence, class_id, track_id in zip(
            boxes,
            confidences,
            class_ids,
            track_ids,
        ):
            x1, y1, x2, y2 = map(float, bbox)

            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0

            tracks.append(
                {
                    "track_id": int(track_id),
                    "bbox": [x1, y1, x2, y2],
                    "confidence": float(confidence),
                    "class_id": int(class_id),
                    "center": [
                        float(center_x),
                        float(center_y),
                    ],
                }
            )

        return {
            "frame_id": frame_id,
            "tracks": tracks,
        }