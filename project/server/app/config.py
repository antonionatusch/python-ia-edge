from __future__ import annotations

import os
from dataclasses import dataclass


def _environment_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    master_url: str
    master_api_token: str
    camera_url: str
    camera_websocket_url: str
    backend_api_token: str
    device_timeout_seconds: float
    debug_classification_interval_seconds: float
    notification_db_path: str = "data/notifications.sqlite3"
    firebase_credentials_path: str | None = None
    round_scheduler_enabled: bool = True
    round_timezone: str = "America/La_Paz"
    round_sample_count: int = 5
    round_sample_interval_seconds: float = 45
    notification_debug_enabled: bool = True
    notification_debug_delay_seconds: float = 5

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            master_url=os.getenv("MASTER_URL", "http://192.168.0.10").rstrip("/"),
            master_api_token=os.getenv("MASTER_API_TOKEN", "change-me"),
            camera_url=os.getenv("CAMERA_URL", "http://192.168.0.11").rstrip("/"),
            camera_websocket_url=os.getenv(
                "CAMERA_WEBSOCKET_URL", "ws://192.168.0.11:81"
            ).rstrip("/"),
            backend_api_token=os.getenv(
                "BACKEND_API_TOKEN", "local-development-token"
            ),
            device_timeout_seconds=float(os.getenv("DEVICE_TIMEOUT_SECONDS", "5")),
            debug_classification_interval_seconds=float(
                os.getenv("DEBUG_CLASSIFICATION_INTERVAL_SECONDS", "5")
            ),
            notification_db_path=os.getenv(
                "NOTIFICATION_DB_PATH", "data/notifications.sqlite3"
            ),
            firebase_credentials_path=os.getenv("FIREBASE_CREDENTIALS_PATH") or None,
            round_scheduler_enabled=_environment_bool(
                "ROUND_SCHEDULER_ENABLED", True
            ),
            round_timezone=os.getenv("ROUND_TIMEZONE", "America/La_Paz"),
            round_sample_count=int(os.getenv("ROUND_SAMPLE_COUNT", "5")),
            round_sample_interval_seconds=float(
                os.getenv("ROUND_SAMPLE_INTERVAL_SECONDS", "45")
            ),
            notification_debug_enabled=_environment_bool(
                "NOTIFICATION_DEBUG_ENABLED", True
            ),
            notification_debug_delay_seconds=float(
                os.getenv("NOTIFICATION_DEBUG_DELAY_SECONDS", "5")
            ),
        )
