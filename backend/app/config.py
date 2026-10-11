import os
from typing import List


class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # SQLite fallback for local dev / testing, PostgreSQL in production
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./traffic.db")

    ALLOWED_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8080,http://localhost:8000",
        ).split(",")
        if origin.strip()
    ]

    # Anomaly baseline thresholds
    Z_SCORE_THRESHOLD: float = float(os.getenv("Z_SCORE_THRESHOLD", "2.5"))
    ERROR_RATE_SURGE_THRESHOLD: float = float(os.getenv("ERROR_RATE_SURGE_THRESHOLD", "0.15"))
    ROLLING_WINDOW_MINUTES: int = int(os.getenv("ROLLING_WINDOW_MINUTES", "15"))

    # Log tailing
    NGINX_LOG_PATH: str = os.getenv("NGINX_LOG_PATH", "/var/log/nginx/access.log")
    TAIL_NGINX_LOGS: bool = os.getenv("TAIL_NGINX_LOGS", "false").lower() == "true"

    # Alert Webhook (Slack / Discord / generic)
    ALERT_WEBHOOK_URL: str = os.getenv("ALERT_WEBHOOK_URL", "")


settings = Settings()
