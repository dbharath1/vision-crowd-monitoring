from app.core.config import settings
from app.core.constants import (
    CONGESTION_HIGH,
    CONGESTION_MODERATE,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
)


class RiskService:
    """
    Application-layer crowd risk indication.

    This is NOT a trained risk classifier.

    Risk is calculated from measurable system outputs:
        - congestion
        - density
        - stationary crowd ratio
        - crowd-group concentration

    No PETS2009 risk labels are assumed.
    """

    def __init__(
        self,
        medium_threshold: float | None = None,
        high_threshold: float | None = None,
    ):
        self.medium_threshold = (
            medium_threshold
            if medium_threshold is not None
            else settings.risk_medium_score
        )

        self.high_threshold = (
            high_threshold
            if high_threshold is not None
            else settings.risk_high_score
        )

        self.high_congestion_weight = (
            settings.risk_high_congestion_weight
        )

        self.density_weight = (
            settings.risk_density_weight
        )

        self.stationary_weight = (
            settings.risk_stationary_weight
        )

        self.group_weight = (
            settings.risk_group_weight
        )

        total_weight = (
            self.high_congestion_weight
            + self.density_weight
            + self.stationary_weight
            + self.group_weight
        )

        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(
                "Risk weights must sum to 1.0."
            )

    # =====================================================
    # MAIN RISK ASSESSMENT
    # =====================================================

    def assess(
        self,
        congestion_result: dict,
        density_result: dict,
        movement_result: dict,
        groups_result: dict,
        behaviour_result: dict | None = None,
    ) -> dict:
        """
        Calculate the current application-layer
        crowd risk indication.
        """

        congestion_level = congestion_result.get(
            "level",
            "NORMAL",
        )

        congestion_score = float(
            congestion_result.get(
                "score",
                0.0,
            )
        )

        density = float(
            density_result.get(
                "density",
                0.0,
            )
        )

        stationary_persons = int(
            movement_result.get(
                "stationary_persons",
                0,
            )
        )

        tracked_persons = int(
            movement_result.get(
                "tracked_persons",
                0,
            )
        )

        groups = groups_result.get(
            "groups",
            [],
        )

        # -------------------------------------------------
        # 1. Congestion component
        # -------------------------------------------------

        congestion_component = (
            self._congestion_component(
                congestion_level,
                congestion_score,
            )
        )

        # -------------------------------------------------
        # 2. Density component
        # -------------------------------------------------

        density_component = (
            self._density_component(
                density,
                congestion_result,
            )
        )

        # -------------------------------------------------
        # 3. Stationary crowd component
        # -------------------------------------------------

        stationary_component = (
            self._stationary_component(
                stationary_persons,
                tracked_persons,
            )
        )

        # -------------------------------------------------
        # 4. Group concentration component
        # -------------------------------------------------

        group_component = (
            self._group_component(
                groups,
                tracked_persons,
            )
        )

        # -------------------------------------------------
        # Combined score
        # -------------------------------------------------

        risk_score = (
            self.high_congestion_weight
            * congestion_component
            +
            self.density_weight
            * density_component
            +
            self.stationary_weight
            * stationary_component
            +
            self.group_weight
            * group_component
        )

        risk_score = min(
            max(risk_score, 0.0),
            1.0,
        )

        risk_level = self._risk_level(
            risk_score
        )

        reasons = self._build_reasons(
            congestion_level=congestion_level,
            congestion_score=congestion_score,
            density_component=density_component,
            stationary_component=stationary_component,
            group_component=group_component,
            behaviour_result=behaviour_result,
        )

        return {
            "level": risk_level,

            "score": float(
                risk_score
            ),

            "reasons": reasons,

            "components": {
                "congestion": float(
                    congestion_component
                ),
                "density": float(
                    density_component
                ),
                "stationary_crowd": float(
                    stationary_component
                ),
                "group_concentration": float(
                    group_component
                ),
            },

            "behaviour": (
                behaviour_result
                if behaviour_result is not None
                else None
            ),

            "ground_truth_available": False,

            "note": (
                "Application-layer risk indication; "
                "not a ground-truth risk classifier."
            ),
        }

    # =====================================================
    # CONGESTION COMPONENT
    # =====================================================

    def _congestion_component(
        self,
        congestion_level: str,
        congestion_score: float,
    ) -> float:

        if congestion_level == CONGESTION_HIGH:
            return 1.0

        if congestion_level == CONGESTION_MODERATE:
            return max(
                congestion_score,
                0.5,
            )

        return congestion_score

    # =====================================================
    # DENSITY COMPONENT
    # =====================================================

    def _density_component(
        self,
        density: float,
        congestion_result: dict,
    ) -> float:

        high_density = float(
            congestion_result.get(
                "components",
                {},
            ).get(
                "density",
                0.0,
            )
        )

        if high_density > 0:
            return min(
                max(high_density, 0.0),
                1.0,
            )

        return min(
            max(density, 0.0),
            1.0,
        )

    # =====================================================
    # STATIONARY COMPONENT
    # =====================================================

    @staticmethod
    def _stationary_component(
        stationary_persons: int,
        tracked_persons: int,
    ) -> float:

        if tracked_persons <= 0:
            return 0.0

        ratio = (
            stationary_persons
            / tracked_persons
        )

        return min(
            max(ratio, 0.0),
            1.0,
        )

    # =====================================================
    # GROUP COMPONENT
    # =====================================================

    @staticmethod
    def _group_component(
        groups: list[dict],
        tracked_persons: int,
    ) -> float:

        if (
            not groups
            or tracked_persons <= 0
        ):
            return 0.0

        largest_group = max(
            (
                int(
                    group.get(
                        "member_count",
                        0,
                    )
                )
                for group in groups
            ),
            default=0,
        )

        concentration = (
            largest_group
            / tracked_persons
        )

        return min(
            max(concentration, 0.0),
            1.0,
        )

    # =====================================================
    # RISK LEVEL
    # =====================================================

    def _risk_level(
        self,
        score: float,
    ) -> str:

        if score >= self.high_threshold:
            return RISK_HIGH

        if score >= self.medium_threshold:
            return RISK_MEDIUM

        return RISK_LOW

    # =====================================================
    # REASONS
    # =====================================================

    def _build_reasons(
        self,
        congestion_level: str,
        congestion_score: float,
        density_component: float,
        stationary_component: float,
        group_component: float,
        behaviour_result: dict | None,
    ) -> list[str]:

        reasons = []

        if congestion_level == CONGESTION_HIGH:
            reasons.append(
                "High congestion detected."
            )

        elif (
            congestion_level
            == CONGESTION_MODERATE
        ):
            reasons.append(
                "Moderate congestion detected."
            )

        if density_component >= 0.70:
            reasons.append(
                "Elevated crowd density."
            )

        if stationary_component >= 0.70:
            reasons.append(
                "Large proportion of tracked people "
                "are stationary."
            )

        if group_component >= 0.70:
            reasons.append(
                "A large proportion of the crowd "
                "is concentrated in one group."
            )

        if behaviour_result:

            behaviour = behaviour_result.get(
                "behaviour"
            )

            status = behaviour_result.get(
                "status"
            )

            if (
                status == "PREDICTED"
                and behaviour
            ):
                reasons.append(
                    f"Behaviour model output: "
                    f"{behaviour}."
                )

        if not reasons:
            reasons.append(
                "No elevated risk indicators "
                "detected from the available measurements."
            )

        return reasons