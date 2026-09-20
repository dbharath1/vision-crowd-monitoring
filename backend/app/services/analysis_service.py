from datetime import datetime

from app.core.config import settings
from app.core.constants import (
    ANALYSIS_COMPLETED,
    ANALYSIS_FAILED,
    ANALYSIS_PROCESSING,
)

from app.services.frame_reader import (
    VideoFrameReader,
    ImageSequenceReader,
)

from app.services.tracking_service import TrackingService
from app.services.trajectory_service import TrajectoryService
from app.services.density_service import DensityService
from app.services.movement_service import MovementService
from app.services.group_service import CrowdGroupService
from app.services.descriptor_service import CrowdDescriptorService
from app.services.behaviour_service import BehaviourService
from app.services.trajectory_behaviour_service import (
    TrajectoryBehaviourService,
)
from app.services.congestion_service import CongestionService
from app.services.risk_service import RiskService
from app.services.alert_service import AlertService


PETS_SOURCE_TYPE = "PETS2009_IMAGE_SEQUENCE"


class AnalysisService:

    def __init__(self, db):

        self.db = db

        # -----------------------------------------
        # Tracking (YOLOv8 + ByteTrack)
        #
        # NOTE: DetectionService is intentionally NOT
        # instantiated here. TrackingService.update()
        # already runs YOLO internally via model.track().
        # Running DetectionService.detect() as well meant
        # every frame was passed through YOLO twice, which
        # doubled runtime for no benefit (PETS views have
        # 700+ frames).
        # -----------------------------------------

        self.tracking_service = TrackingService()

        self.trajectory_service = TrajectoryService()

        self.density_service = DensityService()

        self.group_service = CrowdGroupService()

        self.descriptor_service = CrowdDescriptorService()

        # -----------------------------------------
        # Baseline behaviour (Random Forest)
        # -----------------------------------------

        self.behaviour_service = BehaviourService()

        # -----------------------------------------
        # Proposed trajectory behaviour model
        #
        # Load the trained model if it exists, otherwise
        # predict() safely returns NOT_EVALUATED and the
        # baseline model is used instead.
        # -----------------------------------------

        self.trajectory_behaviour_service = (
            TrajectoryBehaviourService(
                model_path=(
                    settings.trajectory_behaviour_model_path
                )
            )
        )

        try:
            self.trajectory_behaviour_service.load()
        except (FileNotFoundError, ValueError):
            pass

        self.congestion_service = CongestionService()

        self.risk_service = RiskService()

        self.alert_service = AlertService()

    # =====================================================
    # FRAME READER SELECTION
    # =====================================================

    def _get_frame_reader(self, session):

        # -----------------------------------------
        # PETS2009 image sequence
        # -----------------------------------------

        if session.source_type == PETS_SOURCE_TYPE:

            reader = ImageSequenceReader(
                session.source_path
            )

            frame_paths = reader.get_frame_paths()

            if not frame_paths:
                raise ValueError(
                    "PETS image sequence contains "
                    "no supported images."
                )

            # Read the first frame only, to obtain
            # width/height metadata.
            first_frame = next(reader.frames())

            # An image sequence carries no FPS metadata.
            # Falling back to None made every speed value
            # None, which flattened the movement chart and
            # forced the congestion movement score to 0.
            # PETS2009 sequences are recorded at 7 fps.
            fps = float(
                settings.image_sequence_fps
            )

            return reader, {
                "width": first_frame["width"],
                "height": first_frame["height"],
                "fps": fps if fps > 0 else None,
                "total_frames": len(frame_paths),
            }

        # -----------------------------------------
        # Normal uploaded video
        # -----------------------------------------

        reader = VideoFrameReader(
            session.source_path
        )

        metadata = reader.metadata()

        return reader, metadata

    # =====================================================
    # PROCESS SESSION
    # =====================================================

    def process_session(
        self,
        session_id: int,
    ):

        from app.models.schemas import (
            AnalysisSession,
            FrameAnalysis,
            TrackRecord,
            CrowdGroup,
            Alert,
        )

        session = (
            self.db.query(AnalysisSession)
            .filter(
                AnalysisSession.id == session_id
            )
            .first()
        )

        if session is None:

            raise ValueError(
                f"Analysis session "
                f"{session_id} not found."
            )

        try:

            # =====================================
            # SESSION START
            # =====================================

            session.status = ANALYSIS_PROCESSING

            session.started_at = datetime.utcnow()

            session.error_message = None

            self.db.commit()

            # =====================================
            # FRAME READER
            # =====================================

            reader, metadata = (
                self._get_frame_reader(session)
            )

            fps = metadata["fps"]

            # =====================================
            # METADATA
            # =====================================

            session.width = metadata["width"]

            session.height = metadata["height"]

            session.fps = fps

            session.total_frames = metadata[
                "total_frames"
            ]

            self.db.commit()

            # =====================================
            # MOVEMENT SERVICE
            # =====================================

            movement_service = MovementService(
                fps=fps
            )

            # =====================================
            # RESET STATEFUL SERVICES
            # =====================================

            self.trajectory_service.clear()

            self.alert_service.clear()

            # =====================================
            # FRAME PROCESSING
            # =====================================

            processed_frames = 0

            for frame_data in reader.frames():

                frame_id = frame_data["frame_id"]

                frame = frame_data["frame"]

                width = frame_data["width"]

                height = frame_data["height"]

                # =================================
                # OPTIONAL FRAME SKIP
                # =================================

                if (
                    settings.frame_skip > 0
                    and (
                        frame_id
                        % (
                            settings.frame_skip + 1
                        )
                        != 0
                    )
                ):
                    continue

                processed_frames += 1

                # =================================
                # 1. YOLOv8 + BYTETRACK
                # =================================

                tracking_result = (
                    self.tracking_service.update(
                        frame,
                        frame_id,
                    )
                )

                tracks = tracking_result["tracks"]

                # =================================
                # 2. TRAJECTORY
                # =================================

                self.trajectory_service.update(
                    tracking_result
                )

                trajectories = (
                    self.trajectory_service
                    .get_all_trajectories()
                )

                # =================================
                # 3. DENSITY
                # =================================

                density_result = (
                    self.density_service.calculate(
                        tracks=tracks,
                        frame_width=width,
                        frame_height=height,
                        monitored_area=None,
                    )
                )

                # =================================
                # 4. MOVEMENT
                # =================================

                movement_results = (
                    movement_service.calculate_all(
                        trajectories
                    )
                )

                movement_summary = (
                    movement_service.aggregate(
                        movement_results
                    )
                )

                # =================================
                # 5. DBSCAN CROWD GROUPS
                # =================================

                group_result = (
                    self.group_service.cluster(
                        tracks
                    )
                )

                groups = (
                    self.group_service
                    .calculate_group_movement(
                        group_result["groups"],
                        movement_results,
                    )
                )

                # =================================
                # 6. CROWD DESCRIPTORS
                # =================================

                descriptors = (
                    self.descriptor_service.calculate(
                        tracks=tracks,
                        movement_results=(
                            movement_results
                        ),
                        frame_width=width,
                        frame_height=height,
                    )
                )

                # =================================
                # 7. BASELINE RANDOM FOREST
                # =================================

                baseline_behaviour = (
                    self.behaviour_service.predict(
                        descriptors
                    )
                )

                # =================================
                # 8. PROPOSED TRAJECTORY BEHAVIOUR
                # =================================

                trajectory_features = (
                    self.trajectory_behaviour_service
                    .extract_features(
                        tracks=tracks,
                        movement_results=(
                            movement_results
                        ),
                        groups_result=group_result,
                    )
                )

                trajectory_behaviour = (
                    self.trajectory_behaviour_service
                    .predict(
                        features=trajectory_features
                    )
                )

                # =================================
                # SELECT BEHAVIOUR RESULT
                # =================================

                if (
                    trajectory_behaviour["status"]
                    != "NOT_EVALUATED"
                ):

                    behaviour_result = (
                        trajectory_behaviour
                    )

                else:

                    behaviour_result = (
                        baseline_behaviour
                    )

                # =================================
                # 9. CONGESTION
                # =================================

                congestion_result = (
                    self.congestion_service.calculate(
                        density_result=density_result,
                        movement_summary=(
                            movement_summary
                        ),
                        groups=groups,
                    )
                )

                # =================================
                # 10. RISK
                #
                # FIX: RiskService exposes assess(),
                # not calculate(), and its parameters
                # are movement_result / groups_result.
                # The old call raised AttributeError on
                # the very first frame, which is why the
                # PETS analysis never produced any data.
                # =================================

                risk_result = (
                    self.risk_service.assess(
                        congestion_result=(
                            congestion_result
                        ),
                        density_result=density_result,
                        movement_result=(
                            movement_summary
                        ),
                        groups_result={
                            "groups": groups
                        },
                        behaviour_result=(
                            behaviour_result
                        ),
                    )
                )

                # =================================
                # 11. ALERTS
                #
                # FIX: AlertService exposes check(),
                # not generate().
                # =================================

                alerts = (
                    self.alert_service.check(
                        frame_id=frame_id,
                        risk_result=risk_result,
                        congestion_result=(
                            congestion_result
                        ),
                    )
                )

                # =================================
                # 12. SAVE FRAME ANALYSIS
                # =================================

                timestamp = None

                if fps:

                    timestamp = frame_id / fps

                frame_record = FrameAnalysis(

                    session_id=session.id,

                    frame_id=frame_id,

                    timestamp=timestamp,

                    person_count=(
                        density_result[
                            "person_count"
                        ]
                    ),

                    density=(
                        density_result["density"]
                    ),

                    average_speed=(
                        movement_summary[
                            "average_speed"
                        ]
                    ),

                    moving_persons=(
                        movement_summary[
                            "moving_persons"
                        ]
                    ),

                    stationary_persons=(
                        movement_summary[
                            "stationary_persons"
                        ]
                    ),

                    group_count=len(groups),

                    irregularity=(
                        descriptors["irregularity"]
                    ),

                    sparsity=(
                        descriptors["sparsity"]
                    ),

                    randomness=(
                        descriptors["randomness"]
                    ),

                    volatility=(
                        descriptors["volatility"]
                    ),

                    congestion_level=(
                        congestion_result["level"]
                    ),

                    congestion_score=(
                        congestion_result["score"]
                    ),

                    risk_level=(
                        risk_result["level"]
                    ),

                    risk_score=(
                        risk_result["score"]
                    ),

                    behaviour=(
                        behaviour_result.get(
                            "behaviour"
                        )
                    ),

                    behaviour_status=(
                        behaviour_result.get(
                            "status"
                        )
                    ),
                )

                self.db.add(frame_record)

                # =================================
                # 13. SAVE TRACKS
                # =================================

                for track in tracks:

                    track_id = track["track_id"]

                    movement = (
                        movement_results.get(
                            track_id,
                            {},
                        )
                    )

                    bbox = track["bbox"]

                    center = track["center"]

                    track_record = TrackRecord(

                        session_id=session.id,

                        frame_id=frame_id,

                        track_id=track_id,

                        x1=float(bbox[0]),

                        y1=float(bbox[1]),

                        x2=float(bbox[2]),

                        y2=float(bbox[3]),

                        center_x=float(center[0]),

                        center_y=float(center[1]),

                        confidence=float(
                            track["confidence"]
                        ),

                        speed=movement.get(
                            "speed"
                        ),

                        displacement=(
                            movement.get(
                                "displacement"
                            )
                        ),

                        direction=(
                            movement.get(
                                "direction"
                            )
                        ),
                    )

                    self.db.add(track_record)

                # =================================
                # 14. SAVE GROUPS
                # =================================

                for group in groups:

                    bbox = group["bounding_box"]

                    centroid = group["centroid"]

                    group_record = CrowdGroup(

                        session_id=session.id,

                        frame_id=frame_id,

                        group_id=group["group_id"],

                        member_count=group[
                            "member_count"
                        ],

                        centroid_x=float(
                            centroid[0]
                        ),

                        centroid_y=float(
                            centroid[1]
                        ),

                        bbox_x1=float(bbox[0]),

                        bbox_y1=float(bbox[1]),

                        bbox_x2=float(bbox[2]),

                        bbox_y2=float(bbox[3]),

                        average_speed=(
                            group["average_speed"]
                        ),

                        average_displacement=(
                            group[
                                "average_displacement"
                            ]
                        ),
                    )

                    self.db.add(group_record)

                # =================================
                # 15. SAVE ALERTS
                # =================================

                for alert in alerts:

                    alert_record = Alert(

                        session_id=session.id,

                        frame_id=frame_id,

                        alert_type=alert[
                            "alert_type"
                        ],

                        severity=alert["severity"],

                        message=alert["message"],

                        reasons=str(
                            alert.get(
                                "reasons",
                                [],
                            )
                        ),

                        timestamp=datetime.utcnow(),

                        acknowledged=False,
                    )

                    self.db.add(alert_record)

                # =================================
                # PERIODIC COMMIT
                #
                # Commit every 15 frames so the
                # dashboard's 3-second poll shows
                # progress while the run is still
                # in flight.
                # =================================

                if processed_frames % 15 == 0:

                    self.db.commit()

            # =====================================
            # ANALYSIS COMPLETED
            # =====================================

            session.status = ANALYSIS_COMPLETED

            session.completed_at = (
                datetime.utcnow()
            )

            self.db.commit()

            return {

                "session_id": session.id,

                "status": ANALYSIS_COMPLETED,

                "processed_frames": (
                    processed_frames
                ),

            }

        except Exception as exc:

            # =====================================
            # ANALYSIS FAILED
            # =====================================

            self.db.rollback()

            session = (
                self.db.query(AnalysisSession)
                .filter(
                    AnalysisSession.id
                    == session_id
                )
                .first()
            )

            if session is not None:

                session.status = ANALYSIS_FAILED

                session.error_message = str(exc)

                session.completed_at = (
                    datetime.utcnow()
                )

                self.db.commit()

            raise
