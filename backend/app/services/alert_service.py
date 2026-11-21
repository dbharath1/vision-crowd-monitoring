
from datetime import datetime, timezone

from app.core.config import settings


class AlertService:
    """
    Generates alerts from actual congestion and risk results.
    Supports HIGH and MODERATE congestion alerts.
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

        self.last_alert_frame = {}
        self.alerts = []

    # ==========================================
    # MAIN ALERT CHECK
    # ==========================================

    def check(
        self,
        frame_id: int,
        risk_result: dict,
        congestion_result: dict,
    ) -> list[dict]:

        generated_alerts = []

        risk_level = risk_result.get("level")
        congestion_level = congestion_result.get("level")

        # HIGH RISK ALERT
        if risk_level == self.risk_level:

            alert = self._create_alert_if_allowed(
                frame_id=frame_id,
                alert_type="HIGH_RISK",
                severity="HIGH",
                message="High crowd risk detected.",
                reason_list=risk_result.get("reasons", []),
            )

            if alert:
                generated_alerts.append(alert)

        # HIGH CONGESTION ALERT
        elif congestion_level == self.congestion_level:

            alert = self._create_alert_if_allowed(
                frame_id=frame_id,
                alert_type="HIGH_CONGESTION",
                severity="HIGH",
                message="High crowd congestion detected.",
                reason_list=[
                    "Congestion level is HIGH."
                ],
            )

            if alert:
                generated_alerts.append(alert)

        # MODERATE CONGESTION WARNING
        elif congestion_level == "MODERATE":

            alert = self._create_alert_if_allowed(
                frame_id=frame_id,
                alert_type="MODERATE_CONGESTION",
                severity="MEDIUM",
                message="Moderate crowd congestion detected.",
                reason_list=[
                    "Congestion score reached the moderate threshold."
                ],
            )

            if alert:
                generated_alerts.append(alert)

        return generated_alerts

    # ==========================================
    # ALERT CREATION
    # ==========================================

    def _create_alert_if_allowed(
        self,
        frame_id: int,
        alert_type: str,
        severity: str,
        message: str,
        reason_list: list[str],
    ) -> dict | None:

        last_frame = self.last_alert_frame.get(alert_type)

        if last_frame is not None:
            if frame_id - last_frame < self.repeat_frames:
                return None

        alert = {
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "reasons": list(reason_list),
            "frame_id": int(frame_id),
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "acknowledged": False,
        }

        self.last_alert_frame[alert_type] = frame_id
        self.alerts.append(alert)

        return alert

    # ==========================================
    # GET ALERTS
    # ==========================================

    def get_alerts(self) -> list[dict]:
        return list(self.alerts)

    # ==========================================
    # CLEAR
    # ==========================================

    def clear(self):
        self.last_alert_frame.clear()
        self.alerts.clear()
