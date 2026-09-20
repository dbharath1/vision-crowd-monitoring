import cv2

from app.services.detection_service import DetectionService


IMAGE_PATH = (
    r"H:\vision-crowd-monitoring\dataset"
    r"\Crowd_PETS09\S2\L1\Time_12-34"
    r"\View_001\frame_0006.jpg"
)

OUTPUT_PATH = (
    r"H:\vision-crowd-monitoring\backend\outputs"
    r"\detection_test.jpg"
)


def main():

    frame = cv2.imread(IMAGE_PATH)

    if frame is None:
        raise RuntimeError(
            f"Unable to read image: {IMAGE_PATH}"
        )

    detector = DetectionService()

    detections = detector.detect(frame)

    print(
        "Detected people:",
        len(detections),
    )

    for detection in detections:

        x1, y1, x2, y2 = map(
            int,
            detection["bbox"],
        )

        cx, cy = map(
            int,
            detection["center"],
        )

        confidence = detection[
            "confidence"
        ]

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2,
        )

        cv2.circle(
            frame,
            (cx, cy),
            4,
            (255, 0, 0),
            -1,
        )

        label = (
            f"person {confidence:.2f}"
        )

        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 10, 0)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    cv2.imwrite(
        OUTPUT_PATH,
        frame,
    )

    print(
        "Output saved to:",
        OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()