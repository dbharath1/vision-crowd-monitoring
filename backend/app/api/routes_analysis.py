from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.models.database import (
    get_db,
    SessionLocal,
)

from app.models.schemas import (
    AnalysisSession,
    FrameAnalysis,
    TrackRecord,
    CrowdGroup,
    Alert,
)

from app.services.analysis_service import (
    AnalysisService,
)


router = APIRouter(
    prefix="/api/analysis",
    tags=["Analysis"],
)


# =====================================================
# BACKGROUND ANALYSIS
# =====================================================

def run_analysis(
    session_id: int,
):

    db = SessionLocal()

    try:

        service = AnalysisService(
            db
        )

        service.process_session(
            session_id
        )

    except Exception as exc:

        print(
            f"Analysis failed for "
            f"session {session_id}: {exc}"
        )

    finally:

        db.close()


# =====================================================
# START ANALYSIS
# =====================================================

@router.post(
    "/start/{session_id}"
)
def start_analysis(

    session_id: int,

    background_tasks: BackgroundTasks,

    db: Session = Depends(get_db),

):

    session = (

        db.query(
            AnalysisSession
        )

        .filter(
            AnalysisSession.id
            == session_id
        )

        .first()

    )

    if session is None:

        raise HTTPException(

            status_code=404,

            detail=(
                "Analysis session "
                "not found."
            ),

        )

    if session.status == "PROCESSING":

        raise HTTPException(

            status_code=409,

            detail=(
                "Analysis is already "
                "running."
            ),

        )

    background_tasks.add_task(

        run_analysis,

        session_id,

    )

    session.status = "PROCESSING"

    db.commit()

    return {

        "session_id": session_id,

        "status": "PROCESSING",

        "message": (
            "Analysis started."
        ),

    }


# =====================================================
# STATUS
# =====================================================

@router.get(
    "/{session_id}/status"
)
def get_status(

    session_id: int,

    db: Session = Depends(get_db),

):

    session = (

        db.query(
            AnalysisSession
        )

        .filter(
            AnalysisSession.id
            == session_id
        )

        .first()

    )

    if session is None:

        raise HTTPException(

            status_code=404,

            detail=(
                "Analysis session "
                "not found."
            ),

        )

    return {

        "session_id": session.id,

        "status": session.status,

        "filename": session.filename,

        "source_type": (
            session.source_type
        ),

        "source_path": (
            session.source_path
        ),

        "width": session.width,

        "height": session.height,

        "fps": session.fps,

        "total_frames": (
            session.total_frames
        ),

        "error_message": (
            session.error_message
        ),

        "created_at": (
            session.created_at
        ),

        "started_at": (
            session.started_at
        ),

        "completed_at": (
            session.completed_at
        ),

    }


# =====================================================
# SUMMARY
# =====================================================

@router.get(
    "/{session_id}/summary"
)
def get_summary(

    session_id: int,

    db: Session = Depends(get_db),

):

    session = (

        db.query(
            AnalysisSession
        )

        .filter(
            AnalysisSession.id
            == session_id
        )

        .first()

    )

    if session is None:

        raise HTTPException(

            status_code=404,

            detail=(
                "Analysis session "
                "not found."
            ),

        )

    latest_frame = (

        db.query(
            FrameAnalysis
        )

        .filter(
            FrameAnalysis.session_id
            == session_id
        )

        .order_by(
            FrameAnalysis.frame_id.desc()
        )

        .first()

    )

    frames_analyzed = (

        db.query(
            FrameAnalysis
        )

        .filter(
            FrameAnalysis.session_id
            == session_id
        )

        .count()

    )

    track_records = (

        db.query(
            TrackRecord
        )

        .filter(
            TrackRecord.session_id
            == session_id
        )

        .count()

    )

    group_records = (

        db.query(
            CrowdGroup
        )

        .filter(
            CrowdGroup.session_id
            == session_id
        )

        .count()

    )

    alert_count = (

        db.query(
            Alert
        )

        .filter(
            Alert.session_id
            == session_id
        )

        .count()

    )

    latest = None

    if latest_frame:

        latest = {

            "frame_id": (
                latest_frame.frame_id
            ),

            "person_count": (
                latest_frame.person_count
            ),

            "density": (
                latest_frame.density
            ),

            "average_speed": (
                latest_frame.average_speed
            ),

            "moving_persons": (
                latest_frame.moving_persons
            ),

            "stationary_persons": (
                latest_frame.stationary_persons
            ),

            "group_count": (
                latest_frame.group_count
            ),

            "irregularity": (
                latest_frame.irregularity
            ),

            "sparsity": (
                latest_frame.sparsity
            ),

            "randomness": (
                latest_frame.randomness
            ),

            "volatility": (
                latest_frame.volatility
            ),

            "congestion_level": (
                latest_frame.congestion_level
            ),

            "congestion_score": (
                latest_frame.congestion_score
            ),

            "risk_level": (
                latest_frame.risk_level
            ),

            "risk_score": (
                latest_frame.risk_score
            ),

            "behaviour": (
                latest_frame.behaviour
            ),

            "behaviour_status": (
                latest_frame.behaviour_status
            ),

        }

    return {

        "session_id": session_id,

        "status": session.status,

        "frames_analyzed": (
            frames_analyzed
        ),

        "track_records": (
            track_records
        ),

        "group_records": (
            group_records
        ),

        "alert_count": (
            alert_count
        ),

        "latest": latest,

    }


# =====================================================
# FRAME DATA
# =====================================================

@router.get(
    "/{session_id}/frames"
)
def get_frames(

    session_id: int,

    skip: int = 0,

    limit: int = 100,

    db: Session = Depends(get_db),

):

    if limit > 1000:

        limit = 1000

    frames = (

        db.query(
            FrameAnalysis
        )

        .filter(
            FrameAnalysis.session_id
            == session_id
        )

        .order_by(
            FrameAnalysis.frame_id
        )

        .offset(skip)

        .limit(limit)

        .all()

    )

    return [

        {

            "frame_id": frame.frame_id,

            "timestamp": frame.timestamp,

            "person_count": (
                frame.person_count
            ),

            "density": (
                frame.density
            ),

            "average_speed": (
                frame.average_speed
            ),

            "moving_persons": (
                frame.moving_persons
            ),

            "stationary_persons": (
                frame.stationary_persons
            ),

            "group_count": (
                frame.group_count
            ),

            "irregularity": (
                frame.irregularity
            ),

            "sparsity": (
                frame.sparsity
            ),

            "randomness": (
                frame.randomness
            ),

            "volatility": (
                frame.volatility
            ),

            "congestion_level": (
                frame.congestion_level
            ),

            "congestion_score": (
                frame.congestion_score
            ),

            "risk_level": (
                frame.risk_level
            ),

            "risk_score": (
                frame.risk_score
            ),

            "behaviour": (
                frame.behaviour
            ),

            "behaviour_status": (
                frame.behaviour_status
            ),

        }

        for frame in frames

    ]


# =====================================================
# TRACKS
# =====================================================

@router.get(
    "/{session_id}/tracks"
)
def get_tracks(

    session_id: int,

    frame_id: int | None = None,

    skip: int = 0,

    limit: int = 1000,

    db: Session = Depends(get_db),

):

    query = (

        db.query(
            TrackRecord
        )

        .filter(
            TrackRecord.session_id
            == session_id
        )

    )

    if frame_id is not None:

        query = query.filter(

            TrackRecord.frame_id
            == frame_id

        )

    tracks = (

        query

        .order_by(

            TrackRecord.frame_id,

            TrackRecord.track_id,

        )

        .offset(skip)

        .limit(limit)

        .all()

    )

    return [

        {

            "frame_id": track.frame_id,

            "track_id": track.track_id,

            "bbox": [

                track.x1,

                track.y1,

                track.x2,

                track.y2,

            ],

            "center": [

                track.center_x,

                track.center_y,

            ],

            "confidence": (
                track.confidence
            ),

            "speed": (
                track.speed
            ),

            "displacement": (
                track.displacement
            ),

            "direction": (
                track.direction
            ),

        }

        for track in tracks

    ]


# =====================================================
# GROUPS
# =====================================================

@router.get(
    "/{session_id}/groups"
)
def get_groups(

    session_id: int,

    frame_id: int | None = None,

    db: Session = Depends(get_db),

):

    query = (

        db.query(
            CrowdGroup
        )

        .filter(
            CrowdGroup.session_id
            == session_id
        )

    )

    if frame_id is not None:

        query = query.filter(

            CrowdGroup.frame_id
            == frame_id

        )

    groups = (

        query

        .order_by(

            CrowdGroup.frame_id,

            CrowdGroup.group_id,

        )

        .all()

    )

    return [

        {

            "frame_id": group.frame_id,

            "group_id": (
                group.group_id
            ),

            "member_count": (
                group.member_count
            ),

            "centroid": [

                group.centroid_x,

                group.centroid_y,

            ],

            "bounding_box": [

                group.bbox_x1,

                group.bbox_y1,

                group.bbox_x2,

                group.bbox_y2,

            ],

            "average_speed": (
                group.average_speed
            ),

            "average_displacement": (
                group.average_displacement
            ),

        }

        for group in groups

    ]


# =====================================================
# ALERTS
# =====================================================

@router.get(
    "/{session_id}/alerts"
)
def get_alerts(

    session_id: int,

    db: Session = Depends(get_db),

):

    alerts = (

        db.query(
            Alert
        )

        .filter(
            Alert.session_id
            == session_id
        )

        .order_by(
            Alert.frame_id
        )

        .all()

    )

    return [

        {

            "id": alert.id,

            "frame_id": (
                alert.frame_id
            ),

            "alert_type": (
                alert.alert_type
            ),

            "severity": (
                alert.severity
            ),

            "message": (
                alert.message
            ),

            "reasons": (
                alert.reasons
            ),

            "timestamp": (
                alert.timestamp
            ),

            "acknowledged": (
                alert.acknowledged
            ),

        }

        for alert in alerts

    ]