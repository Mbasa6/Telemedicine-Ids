"""Hybrid risk scoring: R = 0.4*A + 0.3*N + 0.2*C + 0.1*F, scaled to 0-100."""
from app.config import settings

ASSET_CRITICALITY_MAP = {
    "admin_console": 1.0,
    "api": 0.8,
    "web_portal": 0.6,
    "mobile_app": 0.4,
}
DEFAULT_ASSET_CRITICALITY = 0.5


def asset_criticality(access_type: str | None) -> float:
    return ASSET_CRITICALITY_MAP.get(access_type, DEFAULT_ASSET_CRITICALITY)


def normalize_frequency(request_frequency: float, max_expected: float = 100.0) -> float:
    return max(0.0, min(1.0, request_frequency / max_expected))


def compute_risk_score(attack_probability: float, anomaly_score: float, criticality: float, frequency_norm: float) -> float:
    w = settings.RISK_WEIGHTS
    a = max(0.0, min(1.0, attack_probability))
    n = max(0.0, min(1.0, anomaly_score))
    c = max(0.0, min(1.0, criticality))
    f = max(0.0, min(1.0, frequency_norm))
    r = (w["attack_probability"] * a) + (w["anomaly_score"] * n) + (w["asset_criticality"] * c) + (w["frequency"] * f)
    return round(r * 100, 2)


def classify_severity(score: float) -> str:
    thresholds = settings.SEVERITY_THRESHOLDS
    if score >= thresholds["critical"]:
        return "critical"
    if score >= thresholds["high"]:
        return "high"
    if score >= thresholds["medium"]:
        return "medium"
    return "low"


def build_explanation(attack_probability, anomaly_score, criticality, frequency_norm, risk_score, severity) -> str:
    return (
        f"Risk score {risk_score}/100 ({severity}). "
        f"Attack probability={attack_probability:.2f}, anomaly score={anomaly_score:.2f}, "
        f"asset criticality={criticality:.2f}, request-frequency factor={frequency_norm:.2f}."
    )
