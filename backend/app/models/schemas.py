from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Column,
)

from sqlalchemy.orm import relationship

from app.models.database import Base


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(Integer, primary_key=True)

    filename = Column(
        String(255),
        nullable=True,
    )

    source_type = Column(
        String(50),
        nullable=False,
    )

    source_path = Column(
        Text,
        nullable=False,
    )

    status = Column(
        String(50),
        nullable=False,
        default="PENDING",
    )

    width = Column(
        Integer,
        nullable=True,
    )

    height = Column(
        Integer,
        nullable=True,
    )

    fps = Column(
        Float,
        nullable=True,
    )

    total_frames = Column(
        Integer,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    started_at = Column(
        DateTime,
        nullable=True,
    )

    completed_at = Column(
        DateTime,
        nullable=True,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    frames = relationship(
        "FrameAnalysis",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    tracks = relationship(
        "TrackRecord",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    groups = relationship(
        "CrowdGroup",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    alerts = relationship(
        "Alert",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class FrameAnalysis(Base):
    __tablename__ = "frame_analysis"

    id = Column(
        Integer,
        primary_key=True,
    )

    session_id = Column(
        Integer,
        ForeignKey(
            "analysis_sessions.id"
        ),
        nullable=False,
    )

    frame_id = Column(
        Integer,
        nullable=False,
    )

    timestamp = Column(
        Float,
        nullable=True,
    )

    person_count = Column(
        Integer,
        default=0,
    )

    density = Column(
        Float,
        nullable=True,
    )

    average_speed = Column(
        Float,
        nullable=True,
    )

    moving_persons = Column(
        Integer,
        default=0,
    )

    stationary_persons = Column(
        Integer,
        default=0,
    )

    group_count = Column(
        Integer,
        default=0,
    )

    irregularity = Column(
        Float,
        nullable=True,
    )

    sparsity = Column(
        Float,
        nullable=True,
    )

    randomness = Column(
        Float,
        nullable=True,
    )

    volatility = Column(
        Float,
        nullable=True,
    )

    congestion_level = Column(
        String(30),
        nullable=True,
    )

    congestion_score = Column(
        Float,
        nullable=True,
    )

    risk_level = Column(
        String(30),
        nullable=True,
    )

    risk_score = Column(
        Float,
        nullable=True,
    )

    behaviour = Column(
        String(100),
        nullable=True,
    )

    behaviour_status = Column(
        String(50),
        nullable=True,
    )

    session = relationship(
        "AnalysisSession",
        back_populates="frames",
    )


class TrackRecord(Base):
    __tablename__ = "tracks"

    id = Column(
        Integer,
        primary_key=True,
    )

    session_id = Column(
        Integer,
        ForeignKey(
            "analysis_sessions.id"
        ),
        nullable=False,
    )

    frame_id = Column(
        Integer,
        nullable=False,
    )

    track_id = Column(
        Integer,
        nullable=False,
    )

    x1 = Column(
        Float,
        nullable=False,
    )

    y1 = Column(
        Float,
        nullable=False,
    )

    x2 = Column(
        Float,
        nullable=False,
    )

    y2 = Column(
        Float,
        nullable=False,
    )

    center_x = Column(
        Float,
        nullable=False,
    )

    center_y = Column(
        Float,
        nullable=False,
    )

    confidence = Column(
        Float,
        nullable=True,
    )

    speed = Column(
        Float,
        nullable=True,
    )

    displacement = Column(
        Float,
        nullable=True,
    )

    direction = Column(
        String(50),
        nullable=True,
    )

    session = relationship(
        "AnalysisSession",
        back_populates="tracks",
    )


class CrowdGroup(Base):
    __tablename__ = "crowd_groups"

    id = Column(
        Integer,
        primary_key=True,
    )

    session_id = Column(
        Integer,
        ForeignKey(
            "analysis_sessions.id"
        ),
        nullable=False,
    )

    frame_id = Column(
        Integer,
        nullable=False,
    )

    group_id = Column(
        Integer,
        nullable=False,
    )

    member_count = Column(
        Integer,
        default=0,
    )

    centroid_x = Column(
        Float,
        nullable=True,
    )

    centroid_y = Column(
        Float,
        nullable=True,
    )

    bbox_x1 = Column(
        Float,
        nullable=True,
    )

    bbox_y1 = Column(
        Float,
        nullable=True,
    )

    bbox_x2 = Column(
        Float,
        nullable=True,
    )

    bbox_y2 = Column(
        Float,
        nullable=True,
    )

    average_speed = Column(
        Float,
        nullable=True,
    )

    average_displacement = Column(
        Float,
        nullable=True,
    )

    session = relationship(
        "AnalysisSession",
        back_populates="groups",
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(
        Integer,
        primary_key=True,
    )

    session_id = Column(
        Integer,
        ForeignKey(
            "analysis_sessions.id"
        ),
        nullable=False,
    )

    frame_id = Column(
        Integer,
        nullable=False,
    )

    alert_type = Column(
        String(100),
        nullable=False,
    )

    severity = Column(
        String(30),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    reasons = Column(
        Text,
        nullable=True,
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
    )

    acknowledged = Column(
        Boolean,
        default=False,
    )

    session = relationship(
        "AnalysisSession",
        back_populates="alerts",
    )