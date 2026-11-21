
from app.core.config import settings


class CongestionService:
    """
    Application-level crowd congestion assessment.

    Uses density, movement, stationary ratio and
    DBSCAN crowd-group concentration.
    """

    def __init__(self):
        self.moderate_density = settings.congestion_density_moderate
        self.high_density = settings.congestion_density_high
        self.low_speed = settings.congestion_speed_low

        self.moderate_score = settings.congestion_moderate_score
        self.high_score = settings.congestion_high_score

    def calculate(
        self,
        density_result: dict,
        movement_summary: dict,
        groups: list[dict],
    ) -> dict:

        density = float(density_result.get("density", 0.0) or 0.0)
        person_count = int(density_result.get("person_count", 0) or 0)

        average_speed = movement_summary.get("average_speed")

        moving = int(movement_summary.get("moving_persons", 0) or 0)
        stationary = int(movement_summary.get("stationary_persons", 0) or 0)
        tracked = moving + stationary

        # 1. Density component
        density_range = self.high_density - self.moderate_density

        if density_range <= 0:
            raise ValueError("High density must exceed moderate density.")

        density_score = self._clamp(
            (density - self.moderate_density) / density_range
        )

        # 2. Slow movement component
        # High speed is not automatically treated as congestion.
        if average_speed is None:
            movement_score = 0.0
        else:
            movement_score = self._clamp(
                1.0 - (float(average_speed) / (self.low_speed * 3.0))
            )

        # 3. Stationary-person component
        stationary_score = (
            self._clamp(stationary / tracked)
            if tracked > 0 else 0.0
        )

        # 4. Crowd-group concentration
        largest_group = max(
            (int(group.get("member_count", 0)) for group in groups),
            default=0,
        )

        group_score = (
            self._clamp(largest_group / person_count)
            if person_count > 0 else 0.0
        )

        # 5. Combined score
        score = self._clamp(
            0.50 * density_score
            + 0.15 * movement_score
            + 0.10 * stationary_score
            + 0.25 * group_score
        )

        # 6. Congestion classification
        if score >= self.high_score:
            level = "HIGH"
        elif score >= self.moderate_score:
            level = "MODERATE"
        else:
            level = "NORMAL"

        return {
            "level": level,
            "score": float(score),
            "person_count": person_count,
            "density": density,
            "average_speed": (
                float(average_speed)
                if average_speed is not None else None
            ),
            "moving_persons": moving,
            "stationary_persons": stationary,
            "stationary_ratio": (
                stationary / tracked if tracked > 0 else 0.0
            ),
            "group_count": len(groups),
            "largest_group_size": largest_group,
            "components": {
                "density_score": float(density_score),
                "movement_score": float(movement_score),
                "stationary_score": float(stationary_score),
                "group_score": float(group_score),
            },
        }

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))
