import numpy as np
import pytest

from app.ml.if_model import IsolationForestDetector
from app.ml.rf_model import RandomForestDetector


@pytest.fixture()
def tmp_model_path(tmp_path):
    return str(tmp_path / "model.joblib")


def _toy_data(n=100):
    rng = np.random.default_rng(42)
    X = rng.normal(size=(n, 5))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    return X, y


def test_random_forest_train_predict_persist(tmp_model_path):
    X, y = _toy_data()
    rf = RandomForestDetector(tmp_model_path)
    rf.train(X, y, feature_names=[f"f{i}" for i in range(5)])
    preds, probs = rf.predict(X)
    assert len(preds) == len(X)
    assert ((probs >= 0) & (probs <= 1)).all()

    rf.save()
    import os
    assert os.path.exists(tmp_model_path)

    reloaded = RandomForestDetector(tmp_model_path)
    assert reloaded.load() is True
    reloaded_preds, _ = reloaded.predict(X)
    assert len(reloaded_preds) == len(X)


def test_random_forest_raises_when_not_trained(tmp_model_path):
    rf = RandomForestDetector(tmp_model_path)
    with pytest.raises(RuntimeError):
        rf.predict(np.zeros((1, 5)))


def test_isolation_forest_scores_in_range(tmp_model_path):
    X, _ = _toy_data()
    iso = IsolationForestDetector(tmp_model_path)
    iso.train(X)
    scores = iso.anomaly_scores(X)
    assert ((scores >= 0) & (scores <= 1)).all()

    iso.save()
    reloaded = IsolationForestDetector(tmp_model_path)
    assert reloaded.load() is True
    reloaded_scores = reloaded.anomaly_scores(X)
    assert len(reloaded_scores) == len(X)


def test_isolation_forest_raises_when_not_trained(tmp_model_path):
    iso = IsolationForestDetector(tmp_model_path)
    with pytest.raises(RuntimeError):
        iso.anomaly_scores(np.zeros((1, 5)))
