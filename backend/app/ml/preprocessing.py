"""Validation/normalisation of ingested CSV event data and feature extraction for ML models."""
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "timestamp", "source_ip", "destination_ip", "user_id",
    "login_attempts", "failed_login_attempts", "request_frequency",
    "session_duration", "data_transfer_volume", "access_type",
    "device_information",
]
OPTIONAL_COLUMNS = ["geo_location", "attack_label"]
NUMERIC_COLUMNS = [
    "login_attempts", "failed_login_attempts", "request_frequency",
    "session_duration", "data_transfer_volume",
]

ACCESS_TYPE_CATEGORIES = ["web_portal", "mobile_app", "api", "admin_console"]
DEVICE_CATEGORIES = ["windows_pc", "mac", "linux", "android", "ios", "unknown"]


def validate_and_normalize(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Validate an uploaded events dataframe. Returns (clean_dataframe, error_messages)."""
    errors: list[str] = []
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return pd.DataFrame(), errors

    clean_rows = []
    for idx, row in df.iterrows():
        row_errors = []

        try:
            ts = pd.to_datetime(row["timestamp"])
            if pd.isna(ts):
                raise ValueError
        except Exception:
            row_errors.append(f"Row {idx}: invalid timestamp '{row.get('timestamp')}'")
            ts = None

        for col in NUMERIC_COLUMNS:
            val = row.get(col)
            try:
                if val is None or (isinstance(val, float) and pd.isna(val)) or str(val).strip() == "":
                    row_errors.append(f"Row {idx}: missing value for '{col}'")
                else:
                    float(val)
            except (ValueError, TypeError):
                row_errors.append(f"Row {idx}: non-numeric value for '{col}' ({val})")

        if not row.get("source_ip") or pd.isna(row.get("source_ip")) or str(row.get("source_ip")).strip() == "":
            row_errors.append(f"Row {idx}: missing source_ip")
        if not row.get("user_id") or pd.isna(row.get("user_id")) or str(row.get("user_id")).strip() == "":
            row_errors.append(f"Row {idx}: missing user_id")

        if row_errors:
            errors.extend(row_errors)
            continue

        clean_rows.append({
            "timestamp": ts,
            "source_ip": str(row["source_ip"]).strip(),
            "destination_ip": str(row.get("destination_ip", "")).strip(),
            "user_id": str(row["user_id"]).strip(),
            "login_attempts": int(float(row["login_attempts"])),
            "failed_login_attempts": int(float(row["failed_login_attempts"])),
            "request_frequency": float(row["request_frequency"]),
            "session_duration": float(row["session_duration"]),
            "data_transfer_volume": float(row["data_transfer_volume"]),
            "access_type": str(row.get("access_type", "unknown")).strip() or "unknown",
            "device_information": str(row.get("device_information", "unknown")).strip() or "unknown",
            "geo_location": (
                str(row.get("geo_location")).strip() if pd.notna(row.get("geo_location")) else None
            ),
            "attack_label": (
                str(row.get("attack_label")).strip() if pd.notna(row.get("attack_label")) else None
            ),
        })

    return pd.DataFrame(clean_rows), errors


def extract_features(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Convert event records into a numeric feature matrix for model training/inference."""
    feature_df = pd.DataFrame(index=df.index)
    feature_df["login_attempts"] = df["login_attempts"].astype(float)
    feature_df["failed_login_attempts"] = df["failed_login_attempts"].astype(float)
    feature_df["failed_ratio"] = (
        df["failed_login_attempts"].astype(float) / df["login_attempts"].astype(float).replace(0, 1)
    ).clip(0, 1)
    feature_df["request_frequency"] = df["request_frequency"].astype(float)
    feature_df["session_duration"] = df["session_duration"].astype(float)
    feature_df["data_transfer_volume"] = df["data_transfer_volume"].astype(float)

    access_type = df["access_type"].fillna("unknown")
    for cat in ACCESS_TYPE_CATEGORIES:
        feature_df[f"access_{cat}"] = (access_type == cat).astype(float)

    device = df["device_information"].fillna("unknown")
    for cat in DEVICE_CATEGORIES:
        feature_df[f"device_{cat}"] = (device == cat).astype(float)

    hour = pd.to_datetime(df["timestamp"]).dt.hour
    feature_df["hour_of_day"] = hour.astype(float)
    feature_df["is_off_hours"] = ((hour < 6) | (hour > 22)).astype(float)

    return feature_df.values, list(feature_df.columns)
