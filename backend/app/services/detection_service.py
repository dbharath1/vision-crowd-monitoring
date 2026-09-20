from pathlib import Path

from ultralytics import YOLO

from app.core.config import settings
from app.core.constants import PERSON_CLASS_ID


class DetectionService:

    def __init__(
        self,
        model_path: str | None = None,
        confidence_threshold: float | None = None,
    ):
        self.model_path = (
            model_path
            or settings.yolo_model_path
        )

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

    def detect(self, frame) -> list[dict]:

        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            verbose=False,
        )

        detections = []

        if not results:
            return detections

        result = results[0]

        if result.boxes is None:
            return detections

        for box in result.boxes:

            class_id = int(
                box.cls[0].item()
            )

            if class_id != PERSON_CLASS_ID:
                continue

            confidence = float(
                box.conf[0].item()
            )

            coordinates = box.xyxy[0].tolist()

            x1, y1, x2, y2 = coordinates

            x1 = float(x1)
            y1 = float(y1)
            x2 = float(x2)
            y2 = float(y2)

            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0

            detections.append(
                {
                    "bbox": [
                        x1,
                        y1,
                        x2,
                        y2,
                    ],
                    "confidence": confidence,
                    "class_id": class_id,
                    "center": [
                        center_x,
                        center_y,
                    ],
                }
            )

        return detections