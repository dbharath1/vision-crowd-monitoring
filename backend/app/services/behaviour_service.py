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

        if self.model_path.exists():
            self.load()

    def _features_to_array(self, descriptors: dict):

        return np.array(
            [[
                float(descriptors.get("irregularity", 0.0)),
                float(descriptors.get("sparsity", 0.0)),
                float(descriptors.get("randomness", 0.0)),
                float(descriptors.get("volatility", 0.0)),
                float(descriptors.get("person_count", 0)),
            ]],
            dtype=float,
        )

    def train(
        self,
        X,
        y,
        save_model: bool = True,
    ):

        X = np.asarray(X, dtype=float)
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

        self.model.fit(X, y)

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

    def predict(
        self,
        descriptors: dict,
    ):

        if self.model is None:

            return {
                "status": "NOT_EVALUATED",
                "behaviour": None,
                "confidence": None,
                "probabilities": {},
                "reason": (
                    "Random Forest model has not "
                    "been trained with labelled data."
                ),
            }

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
                str(class_name): float(probability)
                for class_name, probability
                in zip(
                    self.model.classes_,
                    probability_values,
                )
            }

        confidence = (
            max(probabilities.values())
            if probabilities
            else None
        )

        return {
            "status": "EVALUATED",
            "behaviour": str(prediction),
            "confidence": confidence,
            "probabilities": probabilities,
        }

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

        predictions = self.model.predict(X)

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