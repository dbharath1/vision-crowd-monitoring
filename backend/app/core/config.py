from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    app_name: str = (
        "Vision Based Crowd Congestion Monitoring "
        "and Risk Assessment"
    )

    # -------------------------------------------------
    # Database
    # -------------------------------------------------

    database_url: str = (
        f"sqlite:///{BASE_DIR / 'crowd_monitoring.db'}"
    )

    # -------------------------------------------------
    # Directories
    # -------------------------------------------------

    upload_dir: str = str(
        BASE_DIR / "uploads"
    )

    output_dir: str = str(
        BASE_DIR / "outputs"
    )

    model_dir: str = str(
        BASE_DIR / "models"
    )

    # -------------------------------------------------
    # Dataset
    # -------------------------------------------------

    dataset_root: str = str(
        BASE_DIR.parent
        / "dataset"
        / "Crowd_PETS09"
    )

    # -------------------------------------------------
    # YOLO
    # -------------------------------------------------

    yolo_model_path: str = str(
        BASE_DIR
        / "models"
        / "yolov8n.pt"
    )

    detection_confidence: float = 0.25

    # -------------------------------------------------
    # Processing
    # -------------------------------------------------

    frame_skip: int = 0
    image_sequence_fps: float = 7.0

    # -------------------------------------------------
    # Area
    # -------------------------------------------------

    monitored_area: float = 1.0

    # -------------------------------------------------
    # DBSCAN
    # -------------------------------------------------

    dbscan_eps: float = 80.0

    dbscan_min_samples: int = 3

    # -------------------------------------------------
    # Congestion
    # -------------------------------------------------

    congestion_density_moderate: float = 0.00002

    congestion_density_high: float = 0.00005

    congestion_speed_low: float = 5.0

    congestion_moderate_score: float = 0.40

    congestion_high_score: float = 0.70

    # -------------------------------------------------
    # Risk
    # -------------------------------------------------

    risk_medium_score: float = 0.40

    risk_high_score: float = 0.70

    risk_high_congestion_weight: float = 0.45

    risk_density_weight: float = 0.25

    risk_stationary_weight: float = 0.15

    risk_group_weight: float = 0.15

    # -------------------------------------------------
    # Alerts
    # -------------------------------------------------

    alert_risk_level: str = "HIGH"

    alert_congestion_level: str = "HIGH"

    alert_repeat_frames: int = 30

    # -------------------------------------------------
    # Behaviour model
    # -------------------------------------------------

    trajectory_behaviour_model_path: str = str(
        BASE_DIR
        / "models"
        / "trajectory_behaviour_model.joblib"
    )

    behaviour_model_path: str = str(
        BASE_DIR
        / "models"
        / "behaviour_random_forest.joblib"
    )

    # -------------------------------------------------
    # Pydantic Settings configuration
    # -------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()