import asyncio
from dataclasses import replace
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from app.config import Settings
from app.notification_devices import NotificationDeviceStore
from app.rounds import RoundCoordinator


SETTINGS = Settings(
    master_url="http://master",
    master_api_token="master-secret",
    camera_url="http://camera",
    camera_websocket_url="ws://camera:81",
    backend_api_token="backend-secret",
    device_timeout_seconds=1,
    debug_classification_interval_seconds=0.01,
)


class RoundDeviceClient:
    def __init__(self, results: list[str]) -> None:
        self.results = results
        self.capture_count = 0
        self.mode = "automatic"
        self.relay_enabled = True

    async def master_status(self) -> dict[str, Any]:
        return {"mode": self.mode, "relay_enabled": self.relay_enabled}

    async def camera_capture_and_classify(self) -> dict[str, Any]:
        label = self.results[self.capture_count]
        self.capture_count += 1
        return {
            "predicted_class": label,
            "confidence": 0.9,
            "frame_id": self.capture_count,
        }


class RecordingSender:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def send(self, **message: Any) -> dict[str, int]:
        self.messages.append(message)
        return {"sent": 1, "failed": 0, "skipped": 0}


@pytest.mark.anyio
async def test_automatic_round_uses_five_samples_and_majority_vote(tmp_path) -> None:
    store = NotificationDeviceStore(str(tmp_path / "notifications.sqlite3"))
    devices = RoundDeviceClient(
        ["food_available", "empty", "food_available", "empty", "food_available"]
    )
    sender = RecordingSender()
    settings = replace(
        SETTINGS,
        round_sample_count=5,
        round_sample_interval_seconds=0,
    )
    coordinator = RoundCoordinator(settings, devices, store, sender)
    scheduled_at = datetime(2026, 7, 31, 8, tzinfo=ZoneInfo("America/La_Paz"))

    result, duplicate = await asyncio.gather(
        coordinator.run_scheduled_round(scheduled_at),
        coordinator.run_scheduled_round(scheduled_at),
    )

    assert result["status"] == "completed"
    assert result["result"] == "food_available"
    assert len(result["classifications"]) == 5
    assert devices.capture_count == 5
    assert duplicate["id"] == result["id"]
    assert sender.messages[0]["data"]["round_id"] == str(result["id"])


@pytest.mark.anyio
async def test_inactive_automatic_round_is_skipped(tmp_path) -> None:
    store = NotificationDeviceStore(str(tmp_path / "notifications.sqlite3"))
    devices = RoundDeviceClient(["empty"] * 5)
    devices.relay_enabled = False
    sender = RecordingSender()
    coordinator = RoundCoordinator(SETTINGS, devices, store, sender)

    result = await coordinator.run_scheduled_round(
        datetime(2026, 7, 31, 9, tzinfo=ZoneInfo("America/La_Paz"))
    )

    assert result["status"] == "skipped"
    assert devices.capture_count == 0
    assert sender.messages == []


@pytest.mark.anyio
async def test_debug_notification_is_sent_after_configured_delay(tmp_path) -> None:
    store = NotificationDeviceStore(str(tmp_path / "notifications.sqlite3"))
    devices = RoundDeviceClient(["empty"])
    sender = RecordingSender()
    settings = replace(SETTINGS, notification_debug_delay_seconds=0)
    coordinator = RoundCoordinator(settings, devices, store, sender)

    scheduled = await coordinator.schedule_debug_notification(
        {"predicted_class": "empty", "confidence": 0.87, "frame_id": 9}
    )
    await asyncio.sleep(0.01)

    assert scheduled["scheduled"] is True
    assert sender.messages[0]["notification_type"] == "debug"
    assert sender.messages[0]["data"]["result"] == "empty"
    detail = store.get_round(scheduled["round_id"])
    assert detail is not None
    assert detail["source"] == "debug"
