from __future__ import annotations

import asyncio
import secrets
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import Response

from .config import Settings
from .devices import DeviceClient, DeviceError
from .models import ModeRequest, RelayRequest


def _device_error_response(error: DeviceError) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={"device": error.device, "reason": error.reason},
    )


def require_api_key(
    request: Request,
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    expected = request.app.state.settings.backend_api_token
    if api_key is None or not secrets.compare_digest(api_key, expected):
        raise HTTPException(status_code=401, detail="invalid_api_key")


def create_app(
    settings: Settings | None = None,
    device_client: DeviceClient | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_environment()
    app = FastAPI(
        title="IA Edge Feeder API",
        version="0.1.0",
        description="Control del ESP32 maestro y diagnostico de la ESP32-CAM.",
    )
    app.state.settings = resolved_settings
    app.state.devices = device_client or DeviceClient(resolved_settings)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/master/status", dependencies=[Depends(require_api_key)])
    async def master_status() -> dict[str, Any]:
        try:
            return await app.state.devices.master_status()
        except DeviceError as error:
            raise _device_error_response(error) from error

    @app.post("/api/v1/master/mode", dependencies=[Depends(require_api_key)])
    async def set_master_mode(command: ModeRequest) -> dict[str, Any]:
        try:
            return await app.state.devices.set_master_mode(command.mode.value)
        except DeviceError as error:
            raise _device_error_response(error) from error

    @app.post(
        "/api/v1/master/debug/relay", dependencies=[Depends(require_api_key)]
    )
    async def set_debug_relay(command: RelayRequest) -> dict[str, Any]:
        try:
            return await app.state.devices.set_debug_relay(command.enabled)
        except DeviceError as error:
            raise _device_error_response(error) from error

    @app.get("/api/v1/camera/status", dependencies=[Depends(require_api_key)])
    async def camera_status() -> dict[str, Any]:
        try:
            return await app.state.devices.camera_status()
        except DeviceError as error:
            raise _device_error_response(error) from error

    @app.get("/api/v1/camera/capture", dependencies=[Depends(require_api_key)])
    async def camera_capture() -> Response:
        try:
            content, content_type = await app.state.devices.camera_capture()
            return Response(
                content=content,
                media_type=content_type,
                headers={"Cache-Control": "no-store"},
            )
        except DeviceError as error:
            raise _device_error_response(error) from error

    @app.get("/api/v1/system/status", dependencies=[Depends(require_api_key)])
    async def system_status() -> dict[str, Any]:
        master, camera = await asyncio.gather(
            app.state.devices.master_status(),
            app.state.devices.camera_status(),
            return_exceptions=True,
        )

        def service_result(result: Any) -> dict[str, Any]:
            if isinstance(result, DeviceError):
                return {
                    "available": False,
                    "error": result.reason,
                }
            if isinstance(result, Exception):
                return {"available": False, "error": "unexpected_error"}
            return {"available": True, "data": result}

        return {
            "master": service_result(master),
            "camera": service_result(camera),
        }

    return app


app = create_app()
