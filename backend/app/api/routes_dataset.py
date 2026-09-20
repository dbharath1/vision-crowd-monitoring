from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_db
from app.models.schemas import AnalysisSession
from app.services.analysis_service import AnalysisService


router = APIRouter(
    prefix="/api/dataset",
    tags=["Dataset"],
)


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def run_dataset_analysis(session_id: int):

    from app.models.database import SessionLocal

    db = SessionLocal()

    try:

        service = AnalysisService(db)

        service.process_session(session_id)

    except Exception as exc:

        # If AnalysisService.__init__ fails (for example the
        # YOLO weights are missing), process_session never
        # runs and the session would otherwise sit at
        # PROCESSING forever while the dashboard polls.
        # Mark it FAILED here so the UI surfaces the reason.

        print(
            f"Dataset analysis failed "
            f"for session {session_id}: {exc}"
        )

        try:

            db.rollback()

            session = (
                db.query(AnalysisSession)
                .filter(
                    AnalysisSession.id == session_id
                )
                .first()
            )

            if (
                session is not None
                and session.status != "FAILED"
            ):

                session.status = "FAILED"

                session.error_message = str(exc)

                db.commit()

        except Exception:

            db.rollback()

    finally:

        db.close()


@router.get("/pets/views")
def list_pets_views():

    dataset_root = Path(
        settings.dataset_root
    )

    if not dataset_root.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                f"PETS dataset root not found: "
                f"{dataset_root}"
            ),
        )

    views = []

    for path in dataset_root.rglob("*"):

        if (
            path.is_dir()
            and path.name.startswith("View_")
        ):

            image_count = 0

            for file in path.iterdir():

                if (
                    file.is_file()
                    and file.suffix.lower()
                    in IMAGE_EXTENSIONS
                ):
                    image_count += 1

            if image_count > 0:

                # Include the parent sequence name so the
                # dropdown can distinguish the many
                # identically named View_001 folders.

                label = (
                    f"{path.parent.name} / "
                    f"{path.name}"
                )

                views.append(
                    {
                        "name": label,
                        "path": str(path),
                        "image_count": image_count,
                    }
                )

    views.sort(
        key=lambda item: item["path"]
    )

    return {
        "dataset_root": str(dataset_root),
        "views": views,
    }


@router.post("/pets/analyze")
def analyze_pets_view(
    view_path: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):

    path = Path(view_path)

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "PETS view directory not found."
            ),
        )

    if not path.is_dir():

        raise HTTPException(
            status_code=400,
            detail=(
                "view_path must be a directory."
            ),
        )

    # Only allow paths inside the configured dataset root,
    # since view_path arrives as a client-supplied query
    # parameter and is opened directly from disk.

    dataset_root = Path(
        settings.dataset_root
    ).resolve()

    resolved = path.resolve()

    if (
        resolved != dataset_root
        and dataset_root
        not in resolved.parents
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "view_path must be inside the "
                "configured PETS dataset root."
            ),
        )

    image_count = sum(
        1
        for file in resolved.iterdir()
        if (
            file.is_file()
            and file.suffix.lower()
            in IMAGE_EXTENSIONS
        )
    )

    if image_count == 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "No supported images found "
                "in the selected PETS view."
            ),
        )

    session = AnalysisSession(

        filename=resolved.name,

        source_type=(
            "PETS2009_IMAGE_SEQUENCE"
        ),

        source_path=str(resolved),

        status="PROCESSING",
    )

    db.add(session)

    db.commit()

    db.refresh(session)

    background_tasks.add_task(
        run_dataset_analysis,
        session.id,
    )

    return {

        "session_id": session.id,

        "source_type": (
            "PETS2009_IMAGE_SEQUENCE"
        ),

        "view": resolved.name,

        "path": str(resolved),

        "image_count": image_count,

        "status": "PROCESSING",
    }
