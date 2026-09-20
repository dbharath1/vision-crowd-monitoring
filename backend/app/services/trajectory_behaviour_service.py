from pathlib import Path

import joblib
import numpy as np

from sklearn.ensemble import RandomForestClassifier

from app.core.constants import BEHAVIOUR_CLASSES


class TrajectoryBehaviourService:
    """
    Proposed trajectory-based behaviour analysis.

    Unlike the baseline classifier, this feature vector uses
    person-level trajectory and crowd-group information.

    No behaviour labels are manually assigned.

    A trained model is required for actual behaviour prediction.
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

    # =====================================================
    # FEATURE EXTRACTION
    # =====================================================

    def extract_features(
        self,
        tracks: list[dict],
        movement_results: dict[int, dict],
        groups_result: dict,
    ) -> dict:
        """
        Extract trajectory and crowd-group features
        from the current analysis state.
        """

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
                    float(movement["speed"])
                )

            if movement.get("displacement") is not None:
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
                directions.append(direction)

        # -------------------------------------------------
        # Movement statistics
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Direction statistics
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Spatial trajectory spread
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Group features
        # -------------------------------------------------

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

        noise_track_ids = groups_result.get(
            "noise_track_ids",
            [],
        )

        noise_ratio = (
            len(noise_track_ids)
            / len(tracks)
            if tracks
            else 0.0
        )

        # -------------------------------------------------
        # Movement ratio
        # -------------------------------------------------

        moving_count = 0
        stationary_count = 0

        for track in tracks:

            track_id = int(
                track["track_id"]
            )

            movement = movement_results.get(
                track_id
            )

            if not movement:
                continue

            if movement.get(
                "direction"
            ) == "STATIONARY":

                stationary_count += 1

            else:
                moving_count += 1

        total_movement_observations = (
            moving_count + stationary_count
        )

        moving_ratio = (
            moving_count
            / total_movement_observations
            if total_movement_observations
            else 0.0
        )

        stationary_ratio = (
            stationary_count
            / total_movement_observations
            if total_movement_observations
            else 0.0
        )

        # -------------------------------------------------
        # Group movement
        # -------------------------------------------------

        group_speeds = [
            group["average_speed"]
            for group in groups
            if group.get("average_speed")
            is not None
        ]

        mean_group_speed = (
            float(np.mean(group_speeds))
            if group_speeds
            else 0.0
        )

        return {
            "mean_speed": mean_speed,
            "speed_std": speed_std,
            "mean_displacement": mean_displacement,
            "displacement_std": displacement_std,
            "direction_diversity": direction_diversity,
            "direction_consistency": direction_consistency,
            "trajectory_spread": trajectory_spread,
            "group_count": float(group_count),
            "largest_group_size": float(
                largest_group_size
            ),
            "group_size_mean": group_size_mean,
            "group_size_std": group_size_std,
            "noise_ratio": float(noise_ratio),
            "moving_ratio": float(moving_ratio),
            "stationary_ratio": float(
                stationary_ratio
            ),
            "mean_group_speed": mean_group_speed,
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
                counts.get(direction, 0) + 1
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
                (centers - centroid) ** 2,
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

        self.model.fit(X, y)

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
    # PREDICT
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

        vector = self.to_vector(
            features
        ).reshape(1, -1)

        prediction = self.model.predict(
            vector
        )[0]

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

            classes = self.model.classes_

            for class_name, probability in zip(
                classes,
                values,
            ):
                probabilities[
                    str(class_name)
                ] = float(probability)

        confidence = (
            max(probabilities.values())
            if probabilities
            else None
        )

        return {
            "status": "PREDICTED",
            "behaviour": str(prediction),
            "confidence": (
                float(confidence)
                if confidence is not None
                else None
            ),
            "probabilities": probabilities,
            "reason": None,
        }