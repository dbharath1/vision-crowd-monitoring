from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import ANALYSIS_PENDING
from app.models.schemas import AnalysisSession
from app.utils.file_utils import (
    generate_stored_filename,
    is_supported_video,
)
from app.utils.video_utils import extract_video_metadata


class VideoService:

    @staticmethod
    async def upload_video(
        file: UploadFile,
        db: Session,
    ) -> AnalysisSession:

        if not file.filename:
            raise ValueError(
                "Filename is missing."
            )

        if not is_supported_video(file.filename):
            raise ValueError(
                "Unsupported video format."
            )

        upload_directory = Path(
            settings.upload_dir
        )

        upload_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_filename = generate_stored_filename(
            file.filename
        )

        video_path = (
            upload_directory / stored_filename
        )

        try:
            with video_path.open("wb") as output:

                while True:
                    chunk = await file.read(1024 * 1024)

                    if not chunk:
                        break

                    output.write(chunk)

        except Exception:
            if video_path.exists():
                video_path.unlink()

            raise

        try:
            metadata = extract_video_metadata(
                str(video_path)
            )

        except Exception:
            if video_path.exists():
                video_path.unlink()

            raise

        session = AnalysisSession(
            id=uuid4().hex,
            filename=file.filename,
            stored_filename=stored_filename,
            width=metadata.width,
            height=metadata.height,
            fps=metadata.fps,
            frame_count=metadata.frame_count,
            duration=metadata.duration,
            status=ANALYSIS_PENDING,
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return session