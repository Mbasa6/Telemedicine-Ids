"""Generate clearly-labelled SYNTHETIC telemedicine security event data for training/testing the
AI-IDS prototype and for demonstrating CSV ingestion. No real patient or hospital data is used."""
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

ACCESS_TYPES = ["web_portal", "mobile_app", "api", "admin_console"]
DEVICES = ["windows_pc", "mac", "linux", "android", "ios", "unknown"]
SA_CITIES = ["Johannesburg,ZA", "Cape Town,ZA", "Durban,ZA", "Pretoria,ZA", "Bloemfontein,ZA", "Port Elizabeth,ZA"]
FOREIGN_LOCATIONS = ["Unknown,RU", "Unknown,CN", "Unknown,NG", "Unknown,BR"]

ATTACK_PROFILES = {
    "normal": dict(weight=0.70, login=(1, 3), failed=(0, 1), freq=(1, 15), duration=(120, 1800), volume=(10, 500)),
    "brute_force": dict(weight=0.10, login=(10, 40), failed=(8, 35), freq=(20, 80), duration=(5, 60), volume=(5, 50)),
    "credential_stuffing": dict(weight=0.08, login=(15, 60), failed=(12, 55), freq=(50, 200), duration=(2, 30), volume=(5, 40)),
    "data_exfiltration": dict(weight=0.06, login=(1, 3), failed=(0, 1), freq=(5, 20), duration=(600, 3600), volume=(2000, 20000)),
    "port_scan_recon": dict(weight=0.03, login=(0, 1), failed=(0, 1), freq=(100, 400), duration=(1, 10), volume=(1, 20)),
    "unusual_access": dict(weight=0.03, login=(1, 5), failed=(0, 3), freq=(5, 30), duration=(30, 300), volume=(50, 1000)),
}


def _rand_ip(internal: bool = False) -> str:
    if internal:
        return f"10.0.{random.randint(0, 5)}.{random.randint(2, 254)}"
    return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def _sample_profile() -> str:
    labels = list(ATTACK_PROFILES.keys())
    weights = [ATTACK_PROFILES[label]["weight"] for label in labels]
    return random.choices(labels, weights=weights, k=1)[0]


def generate_events(n_rows: int, start_time: datetime) -> pd.DataFrame:
    rows = []
    for _ in range(n_rows):
        label = _sample_profile()
        profile = ATTACK_PROFILES[label]
        ts = start_time + timedelta(seconds=random.randint(0, 30 * 24 * 3600))
        is_attack = label != "normal"
        geo = random.choice(FOREIGN_LOCATIONS) if (is_attack and random.random() < 0.6) else random.choice(SA_CITIES)

        rows.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "source_ip": _rand_ip(internal=False),
            "destination_ip": _rand_ip(internal=True),
            "user_id": (
                f"patient_{random.randint(1000, 9999)}" if random.random() < 0.7
                else f"clinician_{random.randint(100, 999)}"
            ),
            "login_attempts": random.randint(*profile["login"]),
            "failed_login_attempts": random.randint(*profile["failed"]),
            "request_frequency": round(random.uniform(*profile["freq"]), 2),
            "session_duration": round(random.uniform(*profile["duration"]), 1),
            "data_transfer_volume": round(random.uniform(*profile["volume"]), 2),
            "access_type": random.choice(ACCESS_TYPES),
            "device_information": random.choice(DEVICES),
            "geo_location": geo,
            "attack_label": label,
        })
    return pd.DataFrame(rows)


def main() -> None:
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(backend_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    full_dataset = generate_events(3000, datetime(2026, 1, 1))
    full_path = os.path.join(data_dir, "synthetic_telemedicine_events.csv")
    full_dataset.to_csv(full_path, index=False)
    print(f"Generated labelled training/testing dataset: {full_path} ({len(full_dataset)} rows)")

    demo_sample = generate_events(40, datetime(2026, 2, 1))
    demo_sample = demo_sample.drop(columns=["attack_label"])  # unlabelled, like real ingestion would be

    # Intentionally inject a few invalid rows to demonstrate ingestion validation
    # (columns cast to object dtype first since pandas 3.x disallows lossy setitem of strings into int64 columns)
    demo_sample["login_attempts"] = demo_sample["login_attempts"].astype(object)
    demo_sample["source_ip"] = demo_sample["source_ip"].astype(object)
    demo_sample["failed_login_attempts"] = demo_sample["failed_login_attempts"].astype(object)
    demo_sample.loc[5, "login_attempts"] = "not_a_number"
    demo_sample.loc[12, "source_ip"] = ""
    demo_sample.loc[20, "failed_login_attempts"] = ""

    sample_path = os.path.join(data_dir, "sample_events.csv")
    demo_sample.to_csv(sample_path, index=False)
    print(f"Generated demo CSV for ingestion testing: {sample_path} ({len(demo_sample)} rows, 3 intentionally invalid)")


if __name__ == "__main__":
    main()
