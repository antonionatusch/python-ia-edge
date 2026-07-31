from __future__ import annotations

from pathlib import Path

import firebase_admin
from firebase_admin import credentials


FIREBASE_APP_NAME = "ia-edge-pet-feeder"


def initialize_firebase(credentials_path: str | None) -> firebase_admin.App | None:
    if credentials_path is None:
        return None

    path = Path(credentials_path)
    if not path.is_file():
        raise RuntimeError(f"Firebase credentials file not found: {path}")

    try:
        return firebase_admin.get_app(FIREBASE_APP_NAME)
    except ValueError:
        credential = credentials.Certificate(path)
        return firebase_admin.initialize_app(
            credential,
            name=FIREBASE_APP_NAME,
        )
