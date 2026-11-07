import pandas as pd

from app.ml.preprocessing import extract_features, validate_and_normalize


def _make_valid_df():
    return pd.DataFrame([{
        "timestamp": "2026-01-01 10:00:00", "source_ip": "10.0.0.5", "destination_ip": "10.0.0.1",
        "user_id": "user1", "login_attempts": 3, "failed_login_attempts": 1, "request_frequency": 12.5,
        "session_duration": 300, "data_transfer_volume": 150.0, "access_type": "web_portal",
        "device_information": "windows_pc", "geo_location": "Johannesburg,ZA", "attack_label": "normal",
    }])


def test_validate_and_normalize_accepts_valid_rows():
    clean_df, errors = validate_and_normalize(_make_valid_df())
    assert len(clean_df) == 1
    assert errors == []


def test_validate_and_normalize_flags_missing_required_columns():
    df = _make_valid_df().drop(columns=["login_attempts"])
    clean_df, errors = validate_and_normalize(df)
    assert clean_df.empty
    assert any("Missing required columns" in e for e in errors)


def test_validate_and_normalize_flags_invalid_numeric_value():
    df = _make_valid_df()
    df["login_attempts"] = df["login_attempts"].astype(object)
    df.loc[0, "login_attempts"] = "not_a_number"
    clean_df, errors = validate_and_normalize(df)
    assert clean_df.empty
    assert any("non-numeric value" in e for e in errors)


def test_validate_and_normalize_flags_missing_ip():
    df = _make_valid_df()
    df.loc[0, "source_ip"] = ""
    clean_df, errors = validate_and_normalize(df)
    assert clean_df.empty
    assert any("missing source_ip" in e for e in errors)


def test_extract_features_shape():
    clean_df, _ = validate_and_normalize(_make_valid_df())
    X, feature_names = extract_features(clean_df)
    assert X.shape[0] == 1
    assert X.shape[1] == len(feature_names)
    assert len(feature_names) > 5
