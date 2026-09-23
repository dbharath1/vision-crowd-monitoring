from pathlib import Path

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

        # -----------------------------------------
        # Validate filename
        # -----------------------------------------

        if not file.filename:
            raise ValueError(
                "Filename is missing."
            )

        # -----------------------------------------
        # Validate video format
        # -----------------------------------------

        if not is_supported_video(file.filename):
            raise ValueError(
                "Unsupported video format."
            )

        # -----------------------------------------
        # Create upload directory
        # -----------------------------------------

        upload_directory = Path(
            settings.upload_dir
        )

        upload_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # -----------------------------------------
        # Generate stored filename
        # -----------------------------------------

        stored_filename = generate_stored_filename(
            file.filename
        )

        video_path = (
            upload_directory / stored_filename
        )

        # -----------------------------------------
        # Save uploaded video
        # -----------------------------------------

        try:

            with video_path.open("wb") as output:

                while True:

                    chunk = await file.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    output.write(chunk)

        except Exception:

            if video_path.exists():
                video_path.unlink()

            raise

        # -----------------------------------------
        # Extract video metadata
        # -----------------------------------------

        try:

            metadata = extract_video_metadata(
                str(video_path)
            )

        except Exception:

            if video_path.exists():
                video_path.unlink()

            raise

        # -----------------------------------------
        # Create database session
        # -----------------------------------------

        session = AnalysisSession(

            # IMPORTANT:
            # id is INTEGER primary key,
            # so let SQLite generate it.
            filename=file.filename,

            # Required by AnalysisSession model
            source_type="CCTV_VIDEO",

            # Path used later by AnalysisService
            source_path=str(video_path),

            status=ANALYSIS_PENDING,

            width=metadata.width,

            height=metadata.height,

            fps=metadata.fps,

            # Model uses total_frames
            total_frames=metadata.frame_count,
        )

        # -----------------------------------------
        # Save to database
        # -----------------------------------------

        db.add(session)

        db.commit()

        db.refresh(session)

        return session