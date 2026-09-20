from datetime import datetime, timezone

from app.core.config import settings
from app.core.constants import (
    CONGESTION_HIGH,
    RISK_HIGH,
)


class AlertService:
    """
    Generates alerts from actual congestion and risk results.

    Alerts are event-based system outputs.

    The service does not create alerts from hard-coded
    sample data.
    """

    def __init__(
        self,
        risk_level: str | None = None,
        congestion_level: str | None = None,
        repeat_frames: int | None = None,
    ):

        self.risk_level = (
            risk_level
            if risk_level is not None
            else settings.alert_risk_level
        )

        self.congestion_level = (
            congestion_level
            if congestion_level is not None
            else settings.alert_congestion_level
        )

        self.repeat_frames = (
            repeat_frames
            if repeat_frames is not None
            else settings.alert_repeat_frames
        )

        if self.repeat_frames < 1:
            raise ValueError(
                "alert_repeat_frames must be at least 1."
            )

        # Track when an alert condition was last emitted.
        self.last_alert_frame = {}

        # Keep alerts generated during the current
        # analysis session.
        self.alerts = []

    # =====================================================
    # MAIN ALERT CHECK
    # =====================================================

    def check(
        self,
        frame_id: int,
        risk_result: dict,
        congestion_result: dict,
    ) -> list[dict]:
        """
        Check the current analysis results and generate
        any required alerts.
        """

        generated_alerts = []

        risk_level = risk_result.get(
            "level"
        )

        congestion_level = congestion_result.get(
            "level"
        )

        # -------------------------------------------------
        # HIGH RISK
        # -------------------------------------------------

        if risk_level == self.risk_level:

            alert = self._create_alert_if_allowed(
                frame_id=frame_id,
                alert_type="HIGH_RISK",
                severity="HIGH",
                message=(
                    "High crowd risk detected."
                ),
                reason_list=risk_result.get(
                    "reasons",
                    [],
                ),
            )

            if alert:
                generated_alerts.append(alert)

        # -------------------------------------------------
        # HIGH CONGESTION
        # -------------------------------------------------

        if (
            congestion_level
            == self.congestion_level
            and risk_level != self.risk_level
        ):

            alert = self._create_alert_if_allowed(
                frame_id=frame_id,
                alert_type="HIGH_CONGESTION",
                severity="HIGH",
                message=(
                    "High crowd congestion detected."
                ),
                reason_list=[
                    "Congestion level is HIGH.",
                ],
            )

            if alert:
                generated_alerts.append(alert)

        return generated_alerts

    # =====================================================
    # ALERT CREATION
    # =====================================================

    def _create_alert_if_allowed(
        self,
        frame_id: int,
        alert_type: str,
        severity: str,
        message: str,
        reason_list: list[str],
    ) -> dict | None:

        last_frame = self.last_alert_frame.get(
            alert_type
        )

        # Avoid repeatedly generating the same alert
        # every frame.
        if last_frame is not None:

            if (
                frame_id - last_frame
                < self.repeat_frames
            ):
                return None

        alert = {
            "alert_type": alert_type,

            "severity": severity,

            "message": message,

            "reasons": list(reason_list),

            "frame_id": int(frame_id),

            "timestamp": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),

            "acknowledged": False,
        }

        self.last_alert_frame[
            alert_type
        ] = frame_id

        self.alerts.append(alert)

        return alert

    # =====================================================
    # GET ALERTS
    # =====================================================

    def get_alerts(self) -> list[dict]:
        """
        Return all alerts generated in the
        current analysis.
        """

        return list(self.alerts)

    # =====================================================
    # CLEAR
    # =====================================================

    def clear(self):
        """
        Reset alert state for a new analysis.
        """

        self.last_alert_frame.clear()
        self.alerts.clear()