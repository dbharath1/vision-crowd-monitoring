from pathlib import Path

import joblib
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

from app.core.config import settings
from app.core.constants import BEHAVIOUR_CLASSES


class BehaviourService:

    FEATURE_NAMES = [
        "irregularity",
        "sparsity",
        "randomness",
        "volatility",
        "person_count",
    ]

    def __init__(self, model_path: str | None = None):

        self.model_path = Path(
            model_path or settings.behaviour_model_path
        )

        self.model = None

        # Load trained model if available
        if self.model_path.exists():
            self.load()

    # =====================================================
    # FEATURE CONVERSION
    # =====================================================

    def _features_to_array(
        self,
        descriptors: dict,
    ):

        return np.array(
            [[
                float(
                    descriptors.get(
                        "irregularity",
                        0.0,
                    )
                ),

                float(
                    descriptors.get(
                        "sparsity",
                        0.0,
                    )
                ),

                float(
                    descriptors.get(
                        "randomness",
                        0.0,
                    )
                ),

                float(
                    descriptors.get(
                        "volatility",
                        0.0,
                    )
                ),

                float(
                    descriptors.get(
                        "person_count",
                        0,
                    )
                ),
            ]],
            dtype=float,
        )

    # =====================================================
    # TRAIN MODEL
    # =====================================================

    def train(
        self,
        X,
        y,
        save_model: bool = True,
    ):

        X = np.asarray(
            X,
            dtype=float,
        )

        y = np.asarray(y)

        if len(X) != len(y):

            raise ValueError(
                "X and y must contain the same number of samples."
            )

        if len(X) == 0:

            raise ValueError(
                "Training data cannot be empty."
            )

        self.model = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            class_weight="balanced",
        )

        self.model.fit(
            X,
            y,
        )

        if save_model:

            self.model_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            joblib.dump(
                self.model,
                self.model_path,
            )

        return {
            "status": "TRAINED",
            "samples": len(X),
            "classes": list(
                self.model.classes_
            ),
            "model_path": str(
                self.model_path
            ),
        }

    # =====================================================
    # LOAD MODEL
    # =====================================================

    def load(self):

        if not self.model_path.exists():

            raise FileNotFoundError(
                f"Behaviour model not found: "
                f"{self.model_path}"
            )

        self.model = joblib.load(
            self.model_path
        )

        return self.model

    # =====================================================
    # RULE-BASED BEHAVIOUR CLASSIFICATION
    # =====================================================

    def classify_rule_based(
        self,
        descriptors: dict,
    ):

        irregularity = float(
            descriptors.get(
                "irregularity",
                0.0,
            )
        )

        sparsity = float(
            descriptors.get(
                "sparsity",
                0.0,
            )
        )

        randomness = float(
            descriptors.get(
                "randomness",
                0.0,
            )
        )

        volatility = float(
            descriptors.get(
                "volatility",
                0.0,
            )
        )

        person_count = int(
            descriptors.get(
                "person_count",
                0,
            )
        )

        # =================================================
        # NO PEOPLE
        # =================================================

        if person_count == 0:

            return {
                "behaviour": "Wandering",
                "confidence": 0.0,
                "reason": "No people detected.",
            }

        # =================================================
        # ONE PERSON
        # =================================================

        if person_count == 1:

            return {
                "behaviour": "Wandering",
                "confidence": 0.70,
                "reason": "Only one person is present.",
            }

        # =================================================
        # WANDERING
        #
        # High directional randomness and volatility
        # =================================================

        if (
            randomness >= 0.65
            and volatility >= 0.45
        ):

            return {
                "behaviour": "Wandering",
                "confidence": 0.85,
                "reason": (
                    "Movement directions are highly "
                    "diverse and irregular."
                ),
            }

        # =================================================
        # WALKING GATHERING
        #
        # People are relatively close while moving
        # =================================================

        if (
            volatility >= 0.35
            and irregularity < 0.50
            and sparsity < 0.45
        ):

            return {
                "behaviour": "Walking Gathering",
                "confidence": 0.80,
                "reason": (
                    "People are relatively close together "
                    "while showing varied movement."
                ),
            }

        # =================================================
        # STANDING GATHERING
        #
        # People are close and movement variation is low
        # =================================================

        if (
            volatility < 0.20
            and randomness < 0.30
            and sparsity < 0.45
        ):

            return {
                "behaviour": "Standing Gathering",
                "confidence": 0.90,
                "reason": (
                    "People are close together with "
                    "relatively consistent movement."
                ),
            }

        # =================================================
        # WALKING GATHERING
        #
        # Moderate density and coordinated movement
        # =================================================

        if (
            sparsity < 0.35
            and irregularity < 0.60
        ):

            return {
                "behaviour": "Walking Gathering",
                "confidence": 0.75,
                "reason": (
                    "People are concentrated in the "
                    "same area with coordinated movement."
                ),
            }

        # =================================================
        # DEFAULT
        # =================================================

        return {
            "behaviour": "Wandering",
            "confidence": 0.65,
            "reason": (
                "Crowd movement does not strongly match "
                "another behaviour category."
            ),
        }

    # =====================================================
    # PREDICT BEHAVIOUR
    # =====================================================

    def predict(
        self,
        descriptors: dict,
    ):

        # =================================================
        # USE RANDOM FOREST IF TRAINED MODEL EXISTS
        # =================================================

        if self.model is not None:

            features = self._features_to_array(
                descriptors
            )

            prediction = self.model.predict(
                features
            )[0]

            probabilities = {}

            if hasattr(
                self.model,
                "predict_proba",
            ):

                probability_values = (
                    self.model.predict_proba(
                        features
                    )[0]
                )

                probabilities = {
                    str(class_name): float(
                        probability
                    )
                    for class_name, probability
                    in zip(
                        self.model.classes_,
                        probability_values,
                    )
                }

            confidence = (
                max(
                    probabilities.values()
                )
                if probabilities
                else None
            )

            return {
                "status": "EVALUATED",
                "behaviour": str(
                    prediction
                ),
                "confidence": confidence,
                "probabilities": probabilities,
                "method": "RANDOM_FOREST",
            }

        # =================================================
        # NO RANDOM FOREST MODEL
        #
        # Use rule-based classification
        # =================================================

        result = self.classify_rule_based(
            descriptors
        )

        return {
            "status": "EVALUATED",
            "behaviour": result[
                "behaviour"
            ],
            "confidence": result[
                "confidence"
            ],
            "probabilities": {},
            "reason": result[
                "reason"
            ],
            "method": "RULE_BASED",
        }

    # =====================================================
    # MODEL EVALUATION
    # =====================================================

    def evaluate(
        self,
        X,
        y,
    ):

        if self.model is None:

            raise ValueError(
                "Behaviour model has not been trained."
            )

        X = np.asarray(
            X,
            dtype=float,
        )

        y = np.asarray(y)

        predictions = self.model.predict(
            X
        )

        return {
            "status": "EVALUATED",

            "accuracy": float(
                accuracy_score(
                    y,
                    predictions,
                )
            ),

            "precision": float(
                precision_score(
                    y,
                    predictions,
                    average="weighted",
                    zero_division=0,
                )
            ),

            "recall": float(
                recall_score(
                    y,
                    predictions,
                    average="weighted",
                    zero_division=0,
                )
            ),

            "micro_f1": float(
                f1_score(
                    y,
                    predictions,
                    average="micro",
                    zero_division=0,
                )
            ),

            "macro_f1": float(
                f1_score(
                    y,
                    predictions,
                    average="macro",
                    zero_division=0,
                )
            ),

            "confusion_matrix": (
                confusion_matrix(
                    y,
                    predictions,
                ).tolist()
            ),
        }