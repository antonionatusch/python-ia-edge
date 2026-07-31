import pytest

from app.firebase_service import FirebaseNotificationSender, initialize_firebase
from app.notification_devices import NotificationDeviceStore


def test_firebase_is_optional() -> None:
    assert initialize_firebase(None) is None


def test_firebase_credentials_path_must_exist(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="Firebase credentials file not found"):
        initialize_firebase(str(tmp_path / "missing.json"))


def test_sender_delivers_to_registered_devices(tmp_path, monkeypatch) -> None:
    store = NotificationDeviceStore(str(tmp_path / "notifications.sqlite3"))
    store.register(
        installation_id="installation-123",
        fcm_token="fcm-token-value-with-enough-characters",
        platform="android",
        device_name=None,
    )
    round_record = store.create_round(
        scheduled_at="2026-07-31T08:00:00-04:00",
        source="automatic",
    )
    sent_messages = []

    def fake_send(message, *, app):
        sent_messages.append((message, app))
        return "projects/test/messages/1"

    monkeypatch.setattr("app.firebase_service.messaging.send", fake_send)
    firebase_app = object()
    sender = FirebaseNotificationSender(firebase_app, store)

    result = sender.send(
        title="Ronda completada",
        body="Hay alimento disponible.",
        data={"type": "round_result", "round_id": str(round_record["id"])},
        notification_type="round_result",
        round_id=round_record["id"],
    )

    assert result == {"sent": 1, "failed": 0, "skipped": 0}
    assert sent_messages[0][0].data["round_id"] == str(round_record["id"])
    assert sent_messages[0][1] is firebase_app
