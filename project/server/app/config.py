from __future__ import annotations

import os
from dataclasses import dataclass


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
        )
