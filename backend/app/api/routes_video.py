from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.video_service import VideoService


router = APIRouter(
    prefix="/api/video",
    tags=["Video"],
)


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        session = await VideoService.upload_video(
            file,
            db,
        )

        return {
            "session_id": session.id,
            "filename": session.filename,
            "status": session.status,
            "metadata": {
                "width": session.width,
                "height": session.height,
                "fps": session.fps,
                "frame_count": session.frame_count,
                "duration": session.duration,
            },
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to process uploaded video.",
        )