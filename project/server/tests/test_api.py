import asyncio
import json
from collections import deque
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.config import Settings
from app.devices import CameraCapture, DeviceError
from app.main import create_app
from app.notification_devices import NotificationDeviceStore


class FakeCameraWebSocket:
    def __init__(self) -> None:
        self.incoming: deque[str | bytes] = deque(
            ["READY", "STREAM_STARTED", b"rgb565-frame"]
        )
        self.sent: list[str] = []
        self.wait_forever = asyncio.Event()

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def recv(self) -> str | bytes:
        if self.incoming:
            return self.incoming.popleft()
        await self.wait_forever.wait()
        raise AssertionError("unreachable")


class FakeCameraStream:
    def __init__(self, websocket: FakeCameraWebSocket) -> None:
        self.websocket = websocket

    async def __aenter__(self) -> FakeCameraWebSocket:
        return self.websocket

    async def __aexit__(self, *args: object) -> None:
        return None


class FakeDeviceClient:
    def __init__(self) -> None:
        self.camera_available = True
        self.master_mode = "manual_on"
        self.relay_enabled = True
        self.capture_count = 0
        self.stream_socket = FakeCameraWebSocket()

    async def master_status(self) -> dict[str, Any]:
        return {
            "device": "esp32-master",
            "mode": self.master_mode,
            "relay_enabled": self.relay_enabled,
        }

    async def set_master_mode(self, mode: str) -> dict[str, Any]:
        return {"mode": mode}

    async def set_debug_relay(self, enabled: bool) -> dict[str, Any]:
        return {"relay_enabled": enabled}

    async def camera_status(self) -> dict[str, Any]:
        if not self.camera_available:
            raise DeviceError("camera", "timeout", 504)
        return {"camera_ready": True}

    async def camera_capture(self) -> CameraCapture:
        self.capture_count += 1
        return CameraCapture(b"BMfake", "image/bmp", str(self.capture_count))

    async def camera_classify(self) -> dict[str, Any]:
        return {
            "status": "classified",
            "predicted_class": "food_available",
            "confidence": 0.98,
            "frame_id": self.capture_count,
        }

    async def camera_capture_and_classify(self) -> dict[str, Any]:
        await self.camera_capture()
        return await self.camera_classify()

    def camera_stream(self) -> FakeCameraStream:
        return FakeCameraStream(self.stream_socket)


SETTINGS = Settings(
    master_url="http://master",
    master_api_token="master-secret",
    camera_url="http://camera",
    camera_websocket_url="ws://camera:81",
    backend_api_token="backend-secret",
    device_timeout_seconds=1,
    debug_classification_interval_seconds=0.01,
)
AUTH_HEADERS = {"X-API-Key": "backend-secret"}


def make_client(
    devices: FakeDeviceClient | None = None,
    notification_devices: NotificationDeviceStore | None = None,
    round_coordinator=None,
) -> TestClient:
    app = create_app(
        SETTINGS,
        devices or FakeDeviceClient(),
        notification_devices,
        round_coordinator,
    )
    return TestClient(app)


def test_health_does_not_require_authentication() -> None:
    response = make_client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_control_endpoints_require_api_key() -> None:
    response = make_client().post(
        "/api/v1/master/mode", json={"mode": "manual_on"}
    )
    assert response.status_code == 401


def test_changes_master_mode() -> None:
    response = make_client().post(
        "/api/v1/master/mode",
        headers=AUTH_HEADERS,
        json={"mode": "automatic"},
    )
    assert response.status_code == 200
    assert response.json() == {"mode": "automatic"}


def test_notification_device_registration_requires_api_key(tmp_path) -> None:
    store = NotificationDeviceStore(str(tmp_path / "notifications.sqlite3"))
    response = make_client(notification_devices=store).post(
        "/api/v1/notifications/devices",
        json={
            "installation_id": "installation-123",
            "fcm_token": "fcm-token-value-with-enough-characters",
            "platform": "android",
        },
    )
    assert response.status_code == 401


def test_registers_and_updates_notification_device(tmp_path) -> None:
    store = NotificationDeviceStore(str(tmp_path / "notifications.sqlite3"))
    client = make_client(notification_devices=store)
    payload = {
        "installation_id": "installation-123",
        "fcm_token": "first-fcm-token-value-with-enough-characters",
        "platform": "android",
        "device_name": "Samsung A35",
    }

    first = client.post(
        "/api/v1/notifications/devices",
        headers=AUTH_HEADERS,
        json=payload,
    )
    payload["fcm_token"] = "rotated-fcm-token-value-with-enough-characters"
    second = client.post(
        "/api/v1/notifications/devices",
        headers=AUTH_HEADERS,
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["installation_id"] == "installation-123"
    assert "fcm_token" not in second.json()

    status = client.get("/api/v1/notifications/status", headers=AUTH_HEADERS)
    assert status.status_code == 200
    assert status.json() == {
        "firebase_configured": False,
        "registered_devices": 1,
        "scheduler_enabled": True,
        "scheduler_running": False,
        "debug_enabled": True,
        "debug_delay_seconds": 5,
    }


def test_lists_rounds_and_returns_round_detail(tmp_path) -> None:
    store = NotificationDeviceStore(str(tmp_path / "notifications.sqlite3"))
    round_record = store.create_round(
        scheduled_at="2026-07-31T08:00:00-04:00",
        source="automatic",
    )
    store.add_classification(
        round_id=round_record["id"],
        sample_index=0,
        result={
            "predicted_class": "food_available",
            "confidence": 0.9,
            "frame_id": 7,
        },
    )
    store.set_round_status(
        round_record["id"],
        "completed",
        result="food_available",
        confidence=0.9,
    )
    client = make_client(notification_devices=store)

    listing = client.get("/api/v1/rounds?limit=5", headers=AUTH_HEADERS)
    detail = client.get(
        f"/api/v1/rounds/{round_record['id']}", headers=AUTH_HEADERS
    )

    assert listing.status_code == 200
    assert listing.json()["items"][0]["result"] == "food_available"
    assert listing.json()["items"][0]["valid_sample_count"] == 1
    assert detail.status_code == 200
    assert detail.json()["classifications"][0]["frame_id"] == "7"


def test_debug_notification_requires_firebase_configuration(tmp_path) -> None:
    store = NotificationDeviceStore(str(tmp_path / "notifications.sqlite3"))
    response = make_client(notification_devices=store).post(
        "/api/v1/notifications/debug",
        headers=AUTH_HEADERS,
        json={
            "predicted_class": "empty",
            "confidence": 0.8,
            "frame_id": 5,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "scheduled": False,
        "reason": "firebase_not_configured",
    }


def test_system_status_reports_powered_off_camera() -> None:
    devices = FakeDeviceClient()
    devices.camera_available = False
    response = make_client(devices).get(
        "/api/v1/system/status", headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    assert response.json()["master"]["available"] is True
    assert response.json()["camera"] == {
        "available": False,
        "error": "timeout",
    }


def test_proxies_camera_capture() -> None:
    response = make_client().get(
        "/api/v1/camera/capture", headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/bmp"
    assert response.headers["x-frame-id"] == "1"
    assert response.content == b"BMfake"


def test_proxies_camera_classification() -> None:
    response = make_client().post(
        "/api/v1/camera/classify", headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    assert response.json()["predicted_class"] == "food_available"


def test_capture_and_classify_uses_a_fresh_frame() -> None:
    response = make_client().post(
        "/api/v1/camera/capture-classify", headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    assert response.json()["frame_id"] == 1


def test_debug_stream_requires_authentication() -> None:
    with pytest.raises(WebSocketDisconnect) as error:
        with make_client().websocket_connect("/api/v1/camera/debug-stream"):
            pass
    assert error.value.code == 1008


def test_debug_stream_requires_manual_on_mode() -> None:
    devices = FakeDeviceClient()
    devices.master_mode = "automatic"

    with make_client(devices).websocket_connect(
        "/api/v1/camera/debug-stream", headers=AUTH_HEADERS
    ) as websocket:
        message = websocket.receive_json()
        assert message["error"] == "debug_mode_required"
        with pytest.raises(WebSocketDisconnect) as error:
            websocket.receive_json()
        assert error.value.code == 1008


def test_debug_stream_forwards_frames_and_classifications() -> None:
    devices = FakeDeviceClient()
    received_frame = False
    classification: dict[str, Any] | None = None

    with make_client(devices).websocket_connect(
        "/api/v1/camera/debug-stream", headers=AUTH_HEADERS
    ) as websocket:
        for _ in range(8):
            message = websocket.receive()
            if message.get("bytes") == b"rgb565-frame":
                received_frame = True
            if message.get("text"):
                payload = json.loads(message["text"])
                if payload.get("type") == "classification":
                    classification = payload["data"]
            if received_frame and classification is not None:
                break

    assert received_frame is True
    assert classification is not None
    assert classification["predicted_class"] == "food_available"
    assert devices.capture_count >= 1
    assert devices.stream_socket.sent[0] == "START"
