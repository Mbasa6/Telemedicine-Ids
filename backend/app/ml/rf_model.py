"""Random Forest classifier for detecting known/labelled suspicious telemedicine access patterns."""
import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier


class RandomForestDetector:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model: RandomForestClassifier | None = None
        self.feature_names: list[str] = []

    def train(self, X, y, feature_names: list[str]) -> RandomForestClassifier:
        self.feature_names = feature_names
        self.model = RandomForestClassifier(
            n_estimators=200, max_depth=12, random_state=42, class_weight="balanced"
        )
        self.model.fit(X, y)
        return self.model

    def predict(self, X):
        if self.model is None:
            raise RuntimeError("RandomForest model is not trained/loaded")
        preds = self.model.predict(X)
        if len(self.model.classes_) > 1:
            probs = self.model.predict_proba(X)[:, 1]
        else:
            probs = np.zeros(len(X))
        return preds, probs

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({"model": self.model, "feature_names": self.feature_names}, self.model_path)

    def load(self) -> bool:
        if not os.path.exists(self.model_path):
            return False
        data = joblib.load(self.model_path)
        self.model = data["model"]
        self.feature_names = data["feature_names"]
        return True

    @property
    def is_trained(self) -> bool:
        return self.model is not None
