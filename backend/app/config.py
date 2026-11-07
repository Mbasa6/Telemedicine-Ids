import os


class Settings:
    APP_NAME = "Telemedicine AI-IDS"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./telemedicine_ids.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

    # Directory where trained model artifacts + evaluation results are persisted
    ML_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml_models")

    # Demo administrator account, seeded on first startup only (see README for limitations)
    DEMO_ADMIN_USERNAME = os.getenv("DEMO_ADMIN_USERNAME", "admin")
    DEMO_ADMIN_PASSWORD = os.getenv("DEMO_ADMIN_PASSWORD", "Admin@12345")
    DEMO_ADMIN_EMAIL = "admin@telemedicine-ids.local"

    SEVERITY_THRESHOLDS = {"critical": 80, "high": 60, "medium": 40, "low": 0}
    RISK_WEIGHTS = {"attack_probability": 0.4, "anomaly_score": 0.3, "asset_criticality": 0.2, "frequency": 0.1}


settings = Settings()
