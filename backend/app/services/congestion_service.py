from app.core.config import settings


class CongestionService:
    """
    Dynamic congestion assessment.

    Congestion is calculated from:
    - crowd density
    - average movement speed
    - stationary-person ratio

    Thresholds are configurable through settings.
    No congestion result is hard-coded.
    """

    def __init__(self):
        self.moderate_density = (
            settings.congestion_density_moderate
        )

        self.high_density = (
            settings.congestion_density_high
        )

        self.low_speed = (
            settings.congestion_speed_low
        )

        self.moderate_score = (
            settings.congestion_moderate_score
        )

        self.high_score = (
            settings.congestion_high_score
        )

    # =====================================================
    # MAIN CONGESTION CALCULATION
    # =====================================================

    def calculate(
        self,
        density_result: dict,
        movement_summary: dict,
        groups: list[dict],
    ) -> dict:
        """
        Calculate congestion dynamically for the current frame.
        """

        density = float(
            density_result.get("density", 0.0) or 0.0
        )

        person_count = int(
            density_result.get("person_count", 0) or 0
        )

        average_speed = movement_summary.get(
            "average_speed"
        )

        moving_persons = int(
            movement_summary.get(
                "moving_persons", 0
            )
            or 0
        )

        stationary_persons = int(
            movement_summary.get(
                "stationary_persons", 0
            )
            or 0
        )

        total_movement_persons = (
            moving_persons + stationary_persons
        )

        # -------------------------------------------------
        # 1. Density score
        # -------------------------------------------------

        if density <= self.moderate_density:
            density_score = 0.0

        elif density >= self.high_density:
            density_score = 1.0

        else:
            density_range = (
                self.high_density
                - self.moderate_density
            )

            density_score = (
                density
                - self.moderate_density
            ) / density_range

        density_score = self._clamp(
            density_score
        )

        # -------------------------------------------------
        # 2. Movement / low-speed score
        # -------------------------------------------------

        if average_speed is None:
            movement_score = 0.0
        elif average_speed <= self.low_speed:
            movement_score = 1.0
        else:
            movement_score = max(
                0.0,
                1.0
                - (
                    average_speed
                    / (self.low_speed * 3.0)
                ),
            )

        movement_score = self._clamp(
            movement_score
        )

        # -------------------------------------------------
        # 3. Stationary-person score
        # -------------------------------------------------

        if total_movement_persons > 0:
            stationary_ratio = (
                stationary_persons
                / total_movement_persons
            )
        else:
            stationary_ratio = 0.0

        stationary_score = self._clamp(
            stationary_ratio
        )

        # -------------------------------------------------
        # 4. Combined congestion score
        # -------------------------------------------------
        #
        # Density receives the largest contribution because
        # congestion fundamentally depends on crowding.
        #
        # Movement and stationary behaviour provide
        # additional evidence.
        # -------------------------------------------------

        score = (
            0.60 * density_score
            + 0.25 * movement_score
            + 0.15 * stationary_score
        )

        score = self._clamp(score)

        # -------------------------------------------------
        # 5. Congestion level
        # -------------------------------------------------

        if score >= self.high_score:
            level = "HIGH"

        elif score >= self.moderate_score:
            level = "MODERATE"

        else:
            level = "NORMAL"

        # -------------------------------------------------
        # 6. Return complete result
        # -------------------------------------------------

        return {
            "level": level,
            "score": float(score),

            "person_count": person_count,
            "density": density,

            "average_speed": (
                float(average_speed)
                if average_speed is not None
                else None
            ),

            "moving_persons": moving_persons,
            "stationary_persons": stationary_persons,

            "stationary_ratio": float(
                stationary_ratio
            ),

            "group_count": len(groups),

            "components": {
                "density_score": float(
                    density_score
                ),
                "movement_score": float(
                    movement_score
                ),
                "stationary_score": float(
                    stationary_score
                ),
            },
        }

    # =====================================================
    # UTILITY
    # =====================================================

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 1.0,
    ) -> float:

        return max(
            minimum,
            min(maximum, float(value)),
        )