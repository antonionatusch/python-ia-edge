from __future__ import annotations

import asyncio
import json
import secrets
import time
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import Response
from websockets.exceptions import WebSocketException

from .config import Settings
from .devices import CameraCapture, DeviceClient, DeviceError
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


def websocket_is_authorized(websocket: WebSocket, expected: str) -> bool:
    api_key = websocket.headers.get("X-API-Key")
    return api_key is not None and secrets.compare_digest(api_key, expected)


def create_app(
    settings: Settings | None = None,
    device_client: DeviceClient | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_environment()
    app = FastAPI(
        title="IA Edge Feeder API",
        version="0.2.0",
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
            capture: CameraCapture = await app.state.devices.camera_capture()
            headers = {"Cache-Control": "no-store"}
            if capture.frame_id is not None:
                headers["X-Frame-Id"] = capture.frame_id
            return Response(
                content=capture.content,
                media_type=capture.content_type,
                headers=headers,
            )
        except DeviceError as error:
            raise _device_error_response(error) from error

    @app.post("/api/v1/camera/classify", dependencies=[Depends(require_api_key)])
    async def camera_classify() -> dict[str, Any]:
        try:
            return await app.state.devices.camera_classify()
        except DeviceError as error:
            raise _device_error_response(error) from error

    @app.post(
        "/api/v1/camera/capture-classify",
        dependencies=[Depends(require_api_key)],
    )
    async def camera_capture_and_classify() -> dict[str, Any]:
        try:
            return await app.state.devices.camera_capture_and_classify()
        except DeviceError as error:
            raise _device_error_response(error) from error

    @app.websocket("/api/v1/camera/debug-stream")
    async def camera_debug_stream(websocket: WebSocket) -> None:
        if not websocket_is_authorized(
            websocket, app.state.settings.backend_api_token
        ):
            await websocket.close(code=1008, reason="invalid_api_key")
            return

        await websocket.accept()
        send_lock = asyncio.Lock()

        async def send_text_message(message: dict[str, Any]) -> None:
            async with send_lock:
                await websocket.send_text(json.dumps(message, separators=(",", ":")))

        async def send_binary_frame(frame: bytes) -> None:
            async with send_lock:
                await websocket.send_bytes(frame)

        try:
            master = await app.state.devices.master_status()
        except DeviceError as error:
            await send_text_message(
                {
                    "type": "stream_error",
                    "error": error.reason,
                    "device": error.device,
                }
            )
            await websocket.close(code=1011, reason="master_unavailable")
            return

        if master.get("mode") != "manual_on" or not master.get("relay_enabled"):
            await send_text_message(
                {
                    "type": "stream_error",
                    "error": "debug_mode_required",
                    "master": {
                        "mode": master.get("mode"),
                        "relay_enabled": bool(master.get("relay_enabled")),
                    },
                }
            )
            await websocket.close(code=1008, reason="debug_mode_required")
            return

        await send_text_message(
            {
                "type": "stream_config",
                "status": "connecting",
                "pixel_format": "RGB565",
                "width": 320,
                "height": 240,
                "classification_interval_seconds": (
                    app.state.settings.debug_classification_interval_seconds
                ),
            }
        )
        stream_started = asyncio.Event()

        try:
            async with app.state.devices.camera_stream() as camera_websocket:
                await camera_websocket.send("START")

                async def forward_camera_messages() -> None:
                    while True:
                        message = await camera_websocket.recv()
                        if isinstance(message, bytes):
                            await send_binary_frame(message)
                            continue

                        if message == "STREAM_STARTED":
                            stream_started.set()
                        await send_text_message(
                            {"type": "camera_status", "message": message}
                        )

                async def publish_classifications() -> None:
                    try:
                        await asyncio.wait_for(
                            stream_started.wait(),
                            timeout=app.state.settings.device_timeout_seconds,
                        )
                    except TimeoutError:
                        await send_text_message(
                            {
                                "type": "classification_error",
                                "error": "stream_start_timeout",
                            }
                        )
                        return

                    while True:
                        cycle_started = time.monotonic()
                        try:
                            result = (
                                await app.state.devices.camera_capture_and_classify()
                            )
                            await send_text_message(
                                {"type": "classification", "data": result}
                            )
                        except DeviceError as error:
                            await send_text_message(
                                {
                                    "type": "classification_error",
                                    "error": error.reason,
                                    "device": error.device,
                                }
                            )

                        elapsed = time.monotonic() - cycle_started
                        await asyncio.sleep(
                            max(
                                0,
                                app.state.settings.debug_classification_interval_seconds
                                - elapsed,
                            )
                        )

                forwarding = asyncio.create_task(forward_camera_messages())
                classifying = asyncio.create_task(publish_classifications())
                tasks = {forwarding, classifying}
                try:
                    done, _ = await asyncio.wait(
                        tasks, return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in done:
                        task.result()
                finally:
                    for task in tasks:
                        task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
                    try:
                        await camera_websocket.send("STOP")
                    except WebSocketException:
                        pass
        except (WebSocketDisconnect, WebSocketException):
            pass
        except OSError as error:
            await send_text_message(
                {"type": "stream_error", "error": str(error), "device": "camera"}
            )
        finally:
            try:
                await websocket.close()
            except RuntimeError:
                pass

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
