from __future__ import annotations

from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging

from .notification_devices import NotificationDeviceStore


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


class FirebaseNotificationSender:
    def __init__(
        self,
        app: firebase_admin.App | None,
        store: NotificationDeviceStore,
    ) -> None:
        self.app = app
        self.store = store

    def send(
        self,
        *,
        title: str,
        body: str,
        data: dict[str, str],
        notification_type: str,
        round_id: int | None,
    ) -> dict[str, int]:
        devices = self.store.enabled_devices()
        summary = {"sent": 0, "failed": 0, "skipped": 0}
        if self.app is None:
            summary["skipped"] = len(devices)
            return summary

        for device in devices:
            installation_id = device["installation_id"]
            try:
                message_id = messaging.send(
                    messaging.Message(
                        notification=messaging.Notification(title=title, body=body),
                        data=data,
                        token=device["fcm_token"],
                    ),
                    app=self.app,
                )
                self.store.record_delivery(
                    round_id=round_id,
                    installation_id=installation_id,
                    notification_type=notification_type,
                    status="sent",
                    message_id=message_id,
                )
                summary["sent"] += 1
            except (
                messaging.UnregisteredError,
                messaging.SenderIdMismatchError,
            ) as error:
                self.store.disable_device(installation_id)
                self.store.record_delivery(
                    round_id=round_id,
                    installation_id=installation_id,
                    notification_type=notification_type,
                    status="failed",
                    error=type(error).__name__,
                )
                summary["failed"] += 1
            except Exception as error:
                self.store.record_delivery(
                    round_id=round_id,
                    installation_id=installation_id,
                    notification_type=notification_type,
                    status="failed",
                    error=type(error).__name__,
                )
                summary["failed"] += 1
        return summary
