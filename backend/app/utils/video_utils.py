from pathlib import Path

import cv2


class VideoMetadata:
    def __init__(
        self,
        width: int,
        height: int,
        fps: float,
        frame_count: int,
        duration: float,
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_count = frame_count
        self.duration = duration

    def to_dict(self):
        return {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "duration": self.duration,
        }


def extract_video_metadata(video_path: str) -> VideoMetadata:
    path = Path(video_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Video file not found: {video_path}"
        )

    capture = cv2.VideoCapture(str(path))

    if not capture.isOpened():
        capture.release()

        raise ValueError(
            "Unable to open the uploaded video."
        )

    width = int(
        capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    fps = float(
        capture.get(cv2.CAP_PROP_FPS)
    )

    frame_count = int(
        capture.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    capture.release()

    if fps <= 0:
        raise ValueError(
            "Invalid video FPS."
        )

    duration = frame_count / fps

    return VideoMetadata(
        width=width,
        height=height,
        fps=fps,
        frame_count=frame_count,
        duration=duration,
    )