from pathlib import Path
from typing import Iterator

import cv2


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


class ImageSequenceReader:

    def __init__(
        self,
        directory: str,
    ):

        self.directory = Path(
            directory
        )

        if not self.directory.exists():

            raise FileNotFoundError(
                "Image sequence directory "
                f"not found: {self.directory}"
            )

        if not self.directory.is_dir():

            raise ValueError(
                "Expected an image sequence "
                f"directory: {self.directory}"
            )

    def get_frame_paths(
        self,
    ) -> list[Path]:

        paths = [

            path

            for path in self.directory.iterdir()

            if (

                path.is_file()

                and path.suffix.lower()
                in SUPPORTED_IMAGE_EXTENSIONS

            )

        ]

        return sorted(paths)

    def frames(
        self,
    ) -> Iterator[dict]:

        frame_paths = (
            self.get_frame_paths()
        )

        if not frame_paths:

            raise ValueError(
                "No supported images found "
                f"in {self.directory}"
            )

        for frame_id, image_path in enumerate(
            frame_paths,
            start=1,
        ):

            frame = cv2.imread(
                str(image_path)
            )

            if frame is None:

                raise ValueError(
                    "Unable to read image: "
                    f"{image_path}"
                )

            height, width = (
                frame.shape[:2]
            )

            yield {

                "frame_id": frame_id,

                "path": str(
                    image_path
                ),

                "frame": frame,

                "width": width,

                "height": height,

            }


class VideoFrameReader:

    def __init__(
        self,
        video_path: str,
    ):

        self.video_path = Path(
            video_path
        )

        if not self.video_path.exists():

            raise FileNotFoundError(
                "Video not found: "
                f"{self.video_path}"
            )

        if not self.video_path.is_file():

            raise ValueError(
                "Expected a video file: "
                f"{self.video_path}"
            )

    def metadata(self) -> dict:

        capture = cv2.VideoCapture(
            str(self.video_path)
        )

        if not capture.isOpened():

            raise ValueError(
                "Unable to open video: "
                f"{self.video_path}"
            )

        width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        fps = float(
            capture.get(
                cv2.CAP_PROP_FPS
            )
        )

        total_frames = int(
            capture.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        capture.release()

        return {

            "width": width,

            "height": height,

            "fps": (
                fps
                if fps > 0
                else None
            ),

            "total_frames": (
                total_frames
            ),

        }

    def frames(
        self,
    ) -> Iterator[dict]:

        capture = cv2.VideoCapture(
            str(self.video_path)
        )

        if not capture.isOpened():

            raise ValueError(
                "Unable to open video: "
                f"{self.video_path}"
            )

        frame_id = 0

        try:

            while True:

                success, frame = (
                    capture.read()
                )

                if not success:

                    break

                frame_id += 1

                height, width = (
                    frame.shape[:2]
                )

                yield {

                    "frame_id": frame_id,

                    "path": str(
                        self.video_path
                    ),

                    "frame": frame,

                    "width": width,

                    "height": height,

                }

        finally:

            capture.release()