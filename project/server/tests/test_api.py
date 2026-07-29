from typing import Any

from fastapi.testclient import TestClient

from app.config import Settings
from app.devices import DeviceError
from app.main import create_app


class FakeDeviceClient:
    camera_available = True

    async def master_status(self) -> dict[str, Any]:
        return {"device": "esp32-master", "relay_enabled": False}

    async def set_master_mode(self, mode: str) -> dict[str, Any]:
        return {"mode": mode}

    async def set_debug_relay(self, enabled: bool) -> dict[str, Any]:
        return {"relay_enabled": enabled}

    async def camera_status(self) -> dict[str, Any]:
        if not self.camera_available:
            raise DeviceError("camera", "timeout", 504)
        return {"camera_ready": True}

    async def camera_capture(self) -> tuple[bytes, str]:
        return b"BMfake", "image/bmp"


SETTINGS = Settings(
    master_url="http://master",
    master_api_token="master-secret",
    camera_url="http://camera",
    backend_api_token="backend-secret",
    device_timeout_seconds=1,
)
AUTH_HEADERS = {"X-API-Key": "backend-secret"}


def make_client(devices: FakeDeviceClient | None = None) -> TestClient:
    app = create_app(SETTINGS, devices or FakeDeviceClient())
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
    assert response.content == b"BMfake"
