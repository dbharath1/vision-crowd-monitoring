from pathlib import Path
from uuid import uuid4


ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
}


def is_supported_video(filename: str) -> bool:
    extension = Path(filename).suffix.lower()

    return extension in ALLOWED_VIDEO_EXTENSIONS


def generate_stored_filename(original_filename: str) -> str:
    extension = Path(original_filename).suffix.lower()

    return f"{uuid4().hex}{extension}"