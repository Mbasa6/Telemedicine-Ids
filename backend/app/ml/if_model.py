"""Isolation Forest for identifying unusual/unknown telemedicine access behaviour (unsupervised)."""
import os

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestDetector:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model: IsolationForest | None = None
        self._score_min = 0.0
        self._score_max = 1.0

    def train(self, X) -> IsolationForest:
        self.model = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
        self.model.fit(X)
        raw_scores = -self.model.score_samples(X)  # higher = more anomalous
        self._score_min, self._score_max = float(raw_scores.min()), float(raw_scores.max())
        return self.model

    def anomaly_scores(self, X) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("IsolationForest model is not trained/loaded")
        raw_scores = -self.model.score_samples(X)
        span = (self._score_max - self._score_min) or 1.0
        normalized = (raw_scores - self._score_min) / span
        return np.clip(normalized, 0.0, 1.0)

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(
            {"model": self.model, "score_min": self._score_min, "score_max": self._score_max}, self.model_path
        )

    def load(self) -> bool:
        if not os.path.exists(self.model_path):
            return False
        data = joblib.load(self.model_path)
        self.model = data["model"]
        self._score_min = data["score_min"]
        self._score_max = data["score_max"]
        return True

    @property
    def is_trained(self) -> bool:
        return self.model is not None
