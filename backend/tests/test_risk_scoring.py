from app.ml.risk_scoring import asset_criticality, classify_severity, compute_risk_score, normalize_frequency


def test_compute_risk_score_bounds():
    assert compute_risk_score(1.0, 1.0, 1.0, 1.0) == 100.0
    assert compute_risk_score(0.0, 0.0, 0.0, 0.0) == 0.0


def test_compute_risk_score_weights():
    # Only attack probability contributes -> should equal its weight * 100
    assert compute_risk_score(1.0, 0.0, 0.0, 0.0) == 40.0
    assert compute_risk_score(0.0, 1.0, 0.0, 0.0) == 30.0
    assert compute_risk_score(0.0, 0.0, 1.0, 0.0) == 20.0
    assert compute_risk_score(0.0, 0.0, 0.0, 1.0) == 10.0


def test_compute_risk_score_clamps_out_of_range_inputs():
    score = compute_risk_score(2.0, -1.0, 5.0, 5.0)
    assert 0.0 <= score <= 100.0


def test_classify_severity_thresholds():
    assert classify_severity(85) == "critical"
    assert classify_severity(65) == "high"
    assert classify_severity(45) == "medium"
    assert classify_severity(10) == "low"


def test_asset_criticality_known_and_unknown():
    assert asset_criticality("admin_console") == 1.0
    assert asset_criticality("unknown_type") == 0.5


def test_normalize_frequency_clamped():
    assert normalize_frequency(0) == 0.0
    assert normalize_frequency(1000, max_expected=100) == 1.0
    assert 0 < normalize_frequency(50, max_expected=100) < 1
