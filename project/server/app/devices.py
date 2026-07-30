from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx
import websockets

from .config import Settings


class DeviceError(RuntimeError):
    def __init__(self, device: str, reason: str, status_code: int = 502) -> None:
        super().__init__(reason)
        self.device = device
        self.reason = reason
        self.status_code = status_code


@dataclass(frozen=True)
class CameraCapture:
    content: bytes
    content_type: str
    frame_id: str | None


class DeviceClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._camera_operation_lock = asyncio.Lock()

    async def _request_json(
        self,
        device: str,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.device_timeout_seconds
            ) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as error:
            raise DeviceError(device, "timeout", 504) from error
        except (httpx.HTTPError, ValueError) as error:
            raise DeviceError(device, str(error)) from error

    async def master_status(self) -> dict[str, Any]:
        return await self._request_json(
            "master", "GET", f"{self.settings.master_url}/api/v1/status"
        )

    async def set_master_mode(self, mode: str) -> dict[str, Any]:
        return await self._request_json(
            "master",
            "POST",
            f"{self.settings.master_url}/api/v1/mode",
            params={"value": mode},
            headers={"X-API-Key": self.settings.master_api_token},
        )

    async def set_debug_relay(self, enabled: bool) -> dict[str, Any]:
        return await self._request_json(
            "master",
            "POST",
            f"{self.settings.master_url}/api/v1/debug/relay",
            params={"enabled": str(enabled).lower()},
            headers={"X-API-Key": self.settings.master_api_token},
        )

    async def camera_status(self) -> dict[str, Any]:
        return await self._request_json(
            "camera", "GET", f"{self.settings.camera_url}/status"
        )

    async def _camera_capture(self) -> CameraCapture:
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.device_timeout_seconds
            ) as client:
                response = await client.get(f"{self.settings.camera_url}/capture")
                response.raise_for_status()
                return CameraCapture(
                    content=response.content,
                    content_type=response.headers.get(
                        "content-type", "application/octet-stream"
                    ),
                    frame_id=response.headers.get("x-frame-id"),
                )
        except httpx.TimeoutException as error:
            raise DeviceError("camera", "timeout", 504) from error
        except httpx.HTTPError as error:
            raise DeviceError("camera", str(error)) from error

    async def camera_capture(self) -> CameraCapture:
        async with self._camera_operation_lock:
            return await self._camera_capture()

    async def _camera_classify(self) -> dict[str, Any]:
        return await self._request_json(
            "camera", "POST", f"{self.settings.camera_url}/classify"
        )

    async def camera_classify(self) -> dict[str, Any]:
        async with self._camera_operation_lock:
            return await self._camera_classify()

    async def camera_capture_and_classify(self) -> dict[str, Any]:
        async with self._camera_operation_lock:
            capture = await self._camera_capture()
            result = await self._camera_classify()
        if (
            capture.frame_id is not None
            and str(result.get("frame_id")) != capture.frame_id
        ):
            raise DeviceError("camera", "frame_id_mismatch")
        return result

    def camera_stream(self):
        return websockets.connect(
            self.settings.camera_websocket_url,
            open_timeout=self.settings.device_timeout_seconds,
            close_timeout=self.settings.device_timeout_seconds,
        )
