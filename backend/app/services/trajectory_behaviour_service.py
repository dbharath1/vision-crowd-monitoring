import math
from pathlib import Path

import joblib
import numpy as np

from sklearn.ensemble import RandomForestClassifier

from app.core.constants import BEHAVIOUR_CLASSES


class TrajectoryBehaviourService:
    """
    Trajectory and crowd-based behaviour analysis.

    Behaviour classes:

        - Wandering
        - Merging
        - Standing Gathering
        - Walking Gathering
        - Dispersing

    A trained Random Forest model can be used when available.

    If no trained model is available, a temporal rule-based
    classifier is used. The temporal classifier compares
    consecutive crowd states to detect merging and dispersing.
    """

    FEATURE_NAMES = [
        "mean_speed",
        "speed_std",
        "mean_displacement",
        "displacement_std",
        "direction_diversity",
        "direction_consistency",
        "trajectory_spread",
        "group_count",
        "largest_group_size",
        "group_size_mean",
        "group_size_std",
        "noise_ratio",
        "moving_ratio",
        "stationary_ratio",
        "mean_group_speed",
    ]

    BEHAVIOUR_CLASSES = [
        "Wandering",
        "Merging",
        "Standing Gathering",
        "Walking Gathering",
        "Dispersing",
    ]

    def __init__(
        self,
        model_path: str | None = None,
        random_state: int = 42,
    ):

        self.model_path = (
            Path(model_path)
            if model_path
            else None
        )

        self.model = RandomForestClassifier(
            n_estimators=250,
            random_state=random_state,
            class_weight="balanced",
        )

        self.is_trained = False

        self.training_classes = []

        # -----------------------------------------
        # Temporal state
        # -----------------------------------------

        self.previous_state = None

        self.previous_behaviour = None

        self.behaviour_streak = 0

        # Number of consecutive frames required
        # before changing the reported behaviour.
        self.min_behaviour_streak = 2

        # Relative spatial change required to classify
        # merging/dispersing.
        self.spatial_change_threshold = 0.08

    # =====================================================
    # RESET TEMPORAL STATE
    # =====================================================

    def reset_temporal_state(self):
        """
        Reset all state associated with the previous frame.

        Must be called before starting a new video/session.
        """

        self.previous_state = None

        self.previous_behaviour = None

        self.behaviour_streak = 0

    # =====================================================
    # FEATURE EXTRACTION
    # =====================================================

    def extract_features(
        self,
        tracks: list[dict],
        movement_results: dict[int, dict],
        groups_result: dict,
    ) -> dict:

        if not tracks:
            return {
                name: 0.0
                for name in self.FEATURE_NAMES
            }

        speeds = []
        displacements = []
        directions = []

        for track in tracks:

            track_id = int(
                track["track_id"]
            )

            movement = movement_results.get(
                track_id
            )

            if movement is None:
                continue

            if movement.get("speed") is not None:

                speeds.append(
                    float(
                        movement["speed"]
                    )
                )

            if movement.get(
                "displacement"
            ) is not None:

                displacements.append(
                    float(
                        movement["displacement"]
                    )
                )

            direction = movement.get(
                "direction"
            )

            if direction not in (
                None,
                "UNKNOWN",
            ):

                directions.append(
                    direction
                )

        # -----------------------------------------
        # Movement statistics
        # -----------------------------------------

        mean_speed = (
            float(np.mean(speeds))
            if speeds
            else 0.0
        )

        speed_std = (
            float(np.std(speeds))
            if speeds
            else 0.0
        )

        mean_displacement = (
            float(np.mean(displacements))
            if displacements
            else 0.0
        )

        displacement_std = (
            float(np.std(displacements))
            if displacements
            else 0.0
        )

        # -----------------------------------------
        # Direction statistics
        # -----------------------------------------

        direction_diversity = (
            len(set(directions))
            / 8.0
            if directions
            else 0.0
        )

        direction_consistency = (
            self._direction_consistency(
                directions
            )
        )

        # -----------------------------------------
        # Current spatial spread
        # -----------------------------------------

        centers = np.array(
            [
                track["center"]
                for track in tracks
            ],
            dtype=float,
        )

        trajectory_spread = (
            self._calculate_spread(
                centers
            )
        )

        # -----------------------------------------
        # Group features
        # -----------------------------------------

        groups = groups_result.get(
            "groups",
            [],
        )

        group_count = len(groups)

        group_sizes = [
            int(group["member_count"])
            for group in groups
        ]

        largest_group_size = (
            max(group_sizes)
            if group_sizes
            else 0
        )

        group_size_mean = (
            float(np.mean(group_sizes))
            if group_sizes
            else 0.0
        )

        group_size_std = (
            float(np.std(group_sizes))
            if group_sizes
            else 0.0
        )

        noise_track_ids = (
            groups_result.get(
                "noise_track_ids",
                [],
            )
        )

        noise_ratio = (
            len(noise_track_ids)
            / len(tracks)
            if tracks
            else 0.0
        )

        # -----------------------------------------
        # Movement ratios
        # -----------------------------------------

        moving_count = 0
        stationary_count = 0

        for track in tracks:

            track_id = int(
                track["track_id"]
            )

            movement = (
                movement_results.get(
                    track_id
                )
            )

            if not movement:
                continue

            direction = movement.get(
                "direction"
            )

            if direction == "STATIONARY":

                stationary_count += 1

            elif direction != "UNKNOWN":

                moving_count += 1

        total_observations = (
            moving_count
            + stationary_count
        )

        moving_ratio = (
            moving_count
            / total_observations
            if total_observations
            else 0.0
        )

        stationary_ratio = (
            stationary_count
            / total_observations
            if total_observations
            else 0.0
        )

        # -----------------------------------------
        # Group movement
        # -----------------------------------------

        group_speeds = [
            group["average_speed"]
            for group in groups
            if group.get(
                "average_speed"
            ) is not None
        ]

        mean_group_speed = (
            float(np.mean(group_speeds))
            if group_speeds
            else 0.0
        )

        return {
            "mean_speed": mean_speed,
            "speed_std": speed_std,
            "mean_displacement": (
                mean_displacement
            ),
            "displacement_std": (
                displacement_std
            ),
            "direction_diversity": (
                direction_diversity
            ),
            "direction_consistency": (
                direction_consistency
            ),
            "trajectory_spread": (
                trajectory_spread
            ),
            "group_count": float(
                group_count
            ),
            "largest_group_size": float(
                largest_group_size
            ),
            "group_size_mean": (
                group_size_mean
            ),
            "group_size_std": (
                group_size_std
            ),
            "noise_ratio": float(
                noise_ratio
            ),
            "moving_ratio": float(
                moving_ratio
            ),
            "stationary_ratio": float(
                stationary_ratio
            ),
            "mean_group_speed": (
                mean_group_speed
            ),
        }

    # =====================================================
    # DIRECTION CONSISTENCY
    # =====================================================

    @staticmethod
    def _direction_consistency(
        directions: list[str],
    ) -> float:

        if not directions:
            return 0.0

        counts = {}

        for direction in directions:

            counts[direction] = (
                counts.get(
                    direction,
                    0,
                )
                + 1
            )

        maximum_count = max(
            counts.values()
        )

        return float(
            maximum_count
            / len(directions)
        )

    # =====================================================
    # SPATIAL SPREAD
    # =====================================================

    @staticmethod
    def _calculate_spread(
        centers: np.ndarray,
    ) -> float:

        if len(centers) <= 1:
            return 0.0

        centroid = np.mean(
            centers,
            axis=0,
        )

        distances = np.sqrt(
            np.sum(
                (
                    centers
                    - centroid
                )
                ** 2,
                axis=1,
            )
        )

        return float(
            np.mean(distances)
        )

    # =====================================================
    # FEATURE VECTOR
    # =====================================================

    def to_vector(
        self,
        features: dict,
    ) -> np.ndarray:

        return np.asarray(
            [
                float(
                    features.get(
                        feature,
                        0.0,
                    )
                )
                for feature in self.FEATURE_NAMES
            ],
            dtype=float,
        )

    # =====================================================
    # TEMPORAL STATE
    # =====================================================

    def _build_temporal_state(
        self,
        tracks: list[dict],
        groups_result: dict,
        features: dict,
    ) -> dict:

        centers = [
            [
                float(track["center"][0]),
                float(track["center"][1]),
            ]
            for track in tracks
        ]

        groups = groups_result.get(
            "groups",
            [],
        )

        group_centroids = [
            [
                float(group["centroid"][0]),
                float(group["centroid"][1]),
            ]
            for group in groups
        ]

        group_sizes = [
            int(group["member_count"])
            for group in groups
        ]

        return {
            "person_count": len(tracks),

            "centers": centers,

            "group_centroids": (
                group_centroids
            ),

            "group_sizes": group_sizes,

            "group_count": len(groups),

            "spread": float(
                features.get(
                    "trajectory_spread",
                    0.0,
                )
            ),

            "moving_ratio": float(
                features.get(
                    "moving_ratio",
                    0.0,
                )
            ),

            "stationary_ratio": float(
                features.get(
                    "stationary_ratio",
                    0.0,
                )
            ),

            "mean_speed": float(
                features.get(
                    "mean_speed",
                    0.0,
                )
            ),

            "direction_diversity": float(
                features.get(
                    "direction_diversity",
                    0.0,
                )
            ),

            "direction_consistency": float(
                features.get(
                    "direction_consistency",
                    0.0,
                )
            ),
        }

    # =====================================================
    # GROUP CENTROID DISTANCE
    # =====================================================

    @staticmethod
    def _average_group_distance(
        centroids: list[list[float]],
    ) -> float:

        if len(centroids) < 2:
            return 0.0

        distances = []

        for i in range(
            len(centroids)
        ):

            for j in range(
                i + 1,
                len(centroids),
            ):

                dx = (
                    centroids[i][0]
                    - centroids[j][0]
                )

                dy = (
                    centroids[i][1]
                    - centroids[j][1]
                )

                distance = math.sqrt(
                    (dx * dx)
                    + (dy * dy)
                )

                distances.append(
                    distance
                )

        if not distances:
            return 0.0

        return float(
            np.mean(distances)
        )

    # =====================================================
    # PERSON SPREAD CHANGE
    # =====================================================

    def _calculate_spread_change(
        self,
        previous_state: dict,
        current_state: dict,
    ) -> float | None:

        previous_spread = float(
            previous_state.get(
                "spread",
                0.0,
            )
        )

        current_spread = float(
            current_state.get(
                "spread",
                0.0,
            )
        )

        if previous_spread <= 1.0:
            return None

        return (
            current_spread
            - previous_spread
        ) / previous_spread

    # =====================================================
    # TEMPORAL BEHAVIOUR
    # =====================================================

    def _classify_temporal(
        self,
        tracks: list[dict],
        movement_results: dict[int, dict],
        groups_result: dict,
        features: dict,
    ) -> tuple[str, str]:

        if not tracks:

            return (
                "Wandering",
                "No active crowd group was detected.",
            )

        current_state = (
            self._build_temporal_state(
                tracks=tracks,
                groups_result=groups_result,
                features=features,
            )
        )

        previous_state = (
            self.previous_state
        )

        groups = groups_result.get(
            "groups",
            [],
        )

        group_count = len(groups)

        largest_group_size = (
            max(
                (
                    int(
                        group[
                            "member_count"
                        ]
                    )
                    for group in groups
                ),
                default=0,
            )
        )

        moving_ratio = features.get(
            "moving_ratio",
            0.0,
        )

        stationary_ratio = features.get(
            "stationary_ratio",
            0.0,
        )

        spread = features.get(
            "trajectory_spread",
            0.0,
        )

        direction_diversity = features.get(
            "direction_diversity",
            0.0,
        )

        direction_consistency = features.get(
            "direction_consistency",
            0.0,
        )

        # -----------------------------------------
        # First frame
        # -----------------------------------------

        if previous_state is None:

            self.previous_state = (
                current_state
            )

            if (
                largest_group_size >= 2
                and stationary_ratio >= 0.60
            ):

                return (
                    "Standing Gathering",
                    "People are spatially grouped "
                    "with predominantly stationary movement.",
                )

            if (
                largest_group_size >= 2
                and moving_ratio >= 0.60
            ):

                return (
                    "Walking Gathering",
                    "People are spatially grouped "
                    "with predominantly moving members.",
                )

            return (
                "Wandering",
                "No strong gathering pattern is "
                "present in the current frame.",
            )

        # -----------------------------------------
        # Detect merging / dispersing
        # -----------------------------------------

        previous_group_count = (
            previous_state.get(
                "group_count",
                0,
            )
        )

        previous_group_distance = (
            self._average_group_distance(
                previous_state.get(
                    "group_centroids",
                    [],
                )
            )
        )

        current_group_distance = (
            self._average_group_distance(
                current_state.get(
                    "group_centroids",
                    [],
                )
            )
        )

        # Multiple groups moving closer.
        if (
            previous_group_count >= 2
            and group_count >= 1
            and current_group_distance > 0
        ):

            if previous_group_distance > 0:

                relative_change = (
                    (
                        current_group_distance
                        - previous_group_distance
                    )
                    / previous_group_distance
                )

                if (
                    relative_change
                    <= -self.spatial_change_threshold
                ):

                    return (
                        "Merging",
                        "Spatial separation between "
                        "crowd groups is decreasing.",
                    )

        # Multiple groups becoming more separated.
        if (
            previous_group_count >= 1
            and group_count >= 2
            and previous_group_distance > 0
        ):

            relative_change = (
                (
                    current_group_distance
                    - previous_group_distance
                )
                / previous_group_distance
            )

            if (
                relative_change
                >= self.spatial_change_threshold
            ):

                return (
                    "Dispersing",
                    "Spatial separation between "
                    "crowd groups is increasing.",
                )

        # -----------------------------------------
        # Person-level spread change
        #
        # Useful when DBSCAN temporarily produces
        # no group because of noise or small crowd
        # size.
        # -----------------------------------------

        spread_change = (
            self._calculate_spread_change(
                previous_state,
                current_state,
            )
        )

        if spread_change is not None:

            if (
                spread_change
                <= -self.spatial_change_threshold
                and moving_ratio >= 0.50
                and len(tracks) >= 2
            ):

                return (
                    "Merging",
                    "Overall crowd spatial spread "
                    "is decreasing while people are moving.",
                )

            if (
                spread_change
                >= self.spatial_change_threshold
                and moving_ratio >= 0.40
                and len(tracks) >= 2
            ):

                return (
                    "Dispersing",
                    "Overall crowd spatial spread "
                    "is increasing while people are moving.",
                )

        # -----------------------------------------
        # Standing gathering
        # -----------------------------------------

        if (
            largest_group_size >= 2
            and stationary_ratio >= 0.60
            and spread <= 250.0
        ):

            return (
                "Standing Gathering",
                "People are spatially grouped "
                "and most members are stationary.",
            )

        # -----------------------------------------
        # Walking gathering
        # -----------------------------------------

        if (
            largest_group_size >= 2
            and moving_ratio >= 0.60
            and spread <= 300.0
        ):

            return (
                "Walking Gathering",
                "People are spatially grouped "
                "and most members are moving.",
            )

        # -----------------------------------------
        # Wandering
        # -----------------------------------------

        if (
            direction_diversity >= 0.50
            and direction_consistency <= 0.60
        ):

            return (
                "Wandering",
                "Movement directions are diverse "
                "with no strong common direction.",
            )

        if (
            group_count == 0
            and len(tracks) <= 2
        ):

            return (
                "Wandering",
                "No stable crowd grouping is detected.",
            )

        # -----------------------------------------
        # Conservative fallback
        # -----------------------------------------

        if (
            moving_ratio >= 0.50
            and largest_group_size >= 2
        ):

            return (
                "Walking Gathering",
                "A moving spatial group is detected.",
            )

        if (
            stationary_ratio >= 0.50
            and largest_group_size >= 2
        ):

            return (
                "Standing Gathering",
                "A mostly stationary spatial group "
                "is detected.",
            )

        return (
            "Wandering",
            "No stronger temporal behaviour pattern "
            "was detected.",
        )

    # =====================================================
    # TEMPORAL PREDICTION
    # =====================================================

    def predict_temporal(
        self,
        tracks: list[dict],
        movement_results: dict[int, dict],
        groups_result: dict,
        features: dict,
    ) -> dict:

        behaviour, reason = (
            self._classify_temporal(
                tracks=tracks,
                movement_results=movement_results,
                groups_result=groups_result,
                features=features,
            )
        )

        # -----------------------------------------
        # Temporal smoothing
        # -----------------------------------------

        if (
            self.previous_behaviour
            == behaviour
        ):

            self.behaviour_streak += 1

        else:

            self.previous_behaviour = (
                behaviour
            )

            self.behaviour_streak = 1

        self.previous_state = (
            self._build_temporal_state(
                tracks=tracks,
                groups_result=groups_result,
                features=features,
            )
        )

        return {
            "status": "PREDICTED",
            "behaviour": behaviour,
            "confidence": None,
            "probabilities": {},
            "reason": reason,
            "method": "TEMPORAL_RULE_BASED",
            "stable": (
                self.behaviour_streak
                >= self.min_behaviour_streak
            ),
        }

    # =====================================================
    # TRAIN
    # =====================================================

    def train(
        self,
        feature_records: list[dict],
        labels: list[str],
    ) -> dict:

        if not feature_records:
            raise ValueError(
                "Training feature records are empty."
            )

        if not labels:
            raise ValueError(
                "Training labels are empty."
            )

        if len(feature_records) != len(labels):

            raise ValueError(
                "Number of feature records and labels "
                "must be equal."
            )

        invalid_labels = [
            label
            for label in labels
            if label not in BEHAVIOUR_CLASSES
        ]

        if invalid_labels:

            raise ValueError(
                "Unknown behaviour labels: "
                f"{invalid_labels}"
            )

        X = np.asarray(
            [
                self.to_vector(record)
                for record in feature_records
            ],
            dtype=float,
        )

        y = np.asarray(
            labels,
            dtype=str,
        )

        unique_classes = sorted(
            set(y.tolist())
        )

        if len(unique_classes) < 2:

            raise ValueError(
                "Training requires at least "
                "two behaviour classes."
            )

        self.model.fit(
            X,
            y,
        )

        self.is_trained = True

        self.training_classes = (
            unique_classes
        )

        if self.model_path:

            self.model_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            joblib.dump(
                self.model,
                self.model_path,
            )

        return {
            "trained": True,
            "samples": len(labels),
            "classes": unique_classes,
            "features": self.FEATURE_NAMES,
        }

    # =====================================================
    # LOAD MODEL
    # =====================================================

    def load(self) -> dict:

        if self.model_path is None:

            raise ValueError(
                "No trajectory behaviour model "
                "path configured."
            )

        if not self.model_path.exists():

            raise FileNotFoundError(
                "Trajectory behaviour model not found: "
                f"{self.model_path}"
            )

        self.model = joblib.load(
            self.model_path
        )

        self.is_trained = True

        if hasattr(
            self.model,
            "classes_",
        ):

            self.training_classes = [
                str(value)
                for value in self.model.classes_
            ]

        return {
            "loaded": True,
            "classes": self.training_classes,
        }

    # =====================================================
    # PREDICT USING TRAINED MODEL
    # =====================================================

    def predict(
        self,
        features: dict,
    ) -> dict:

        if not self.is_trained:

            return {
                "status": "NOT_EVALUATED",
                "behaviour": None,
                "confidence": None,
                "probabilities": {},
                "reason": (
                    "Trajectory behaviour model "
                    "has not been trained with "
                    "labelled data."
                ),
            }

        vector = (
            self.to_vector(
                features
            )
            .reshape(1, -1)
        )

        prediction = (
            self.model.predict(
                vector
            )[0]
        )

        probabilities = {}

        if hasattr(
            self.model,
            "predict_proba",
        ):

            values = (
                self.model.predict_proba(
                    vector
                )[0]
            )

            classes = (
                self.model.classes_
            )

            for (
                class_name,
                probability,
            ) in zip(
                classes,
                values,
            ):

                probabilities[
                    str(class_name)
                ] = float(
                    probability
                )

        confidence = (
            max(
                probabilities.values()
            )
            if probabilities
            else None
        )

        return {
            "status": "PREDICTED",
            "behaviour": str(
                prediction
            ),
            "confidence": (
                float(confidence)
                if confidence is not None
                else None
            ),
            "probabilities": probabilities,
            "reason": None,
            "method": "RANDOM_FOREST",
        }