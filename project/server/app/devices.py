from __future__ import annotations

from typing import Any

import httpx

from .config import Settings


class DeviceError(RuntimeError):
    def __init__(self, device: str, reason: str, status_code: int = 502) -> None:
        super().__init__(reason)
        self.device = device
        self.reason = reason
        self.status_code = status_code


class DeviceClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

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

    async def camera_capture(self) -> tuple[bytes, str]:
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.device_timeout_seconds
            ) as client:
                response = await client.get(f"{self.settings.camera_url}/capture")
                response.raise_for_status()
                return response.content, response.headers.get(
                    "content-type", "application/octet-stream"
                )
        except httpx.TimeoutException as error:
            raise DeviceError("camera", "timeout", 504) from error
        except httpx.HTTPError as error:
            raise DeviceError("camera", str(error)) from error
