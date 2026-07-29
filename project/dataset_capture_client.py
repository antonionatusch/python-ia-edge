#!/usr/bin/env python3
"""Interactive WebSocket dataset collector for the ESP32-CAM GC2145 server."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import cv2
import numpy as np
import requests
import websockets
from websockets.exceptions import WebSocketException

CLASSES = ("empty", "food_available", "unknown")
ZOOM_LEVELS = (1.0, 1.25, 1.5, 2.0)
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
EXPECTED_RGB565_BYTES = FRAME_WIDTH * FRAME_HEIGHT * 2
METADATA_FIELDS = (
    "sample_id",
    "class",
    "captured_at",
    "sequence",
    "variant",
    "filename",
    "zoom",
    "zoom_applied",
    "enhancement",
    "source_width",
    "source_height",
    "source_sha256",
    "difference_from_previous",
    "esp32_url",
)


@dataclass(frozen=True)
class Capture:
    original: np.ndarray
    processed: np.ndarray
    zoom: float
    source_sha256: str
    difference_from_previous: float | None


@dataclass
class StreamState:
    class_index: int = 0
    zoom_index: int = 0
    last_saved_original: np.ndarray | None = None


class DatasetManager:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.metadata_path = root / "metadata.csv"
        self.counts = {class_name: 0 for class_name in CLASSES}
        self.next_sequences = {class_name: 1 for class_name in CLASSES}
        self._known_sample_ids: set[str] = set()
        self._prepare()

    def _prepare(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for class_name in CLASSES:
            (self.root / class_name).mkdir(exist_ok=True)

        # 1) Read existing CSV rows keyed by sample_id.
        csv_rows: dict[str, dict[str, str]] = {}
        if self.metadata_path.exists():
            try:
                with self.metadata_path.open("r", newline="", encoding="utf-8") as file:
                    for row in csv.DictReader(file):
                        sample_id = row.get("sample_id", "")
                        csv_rows[sample_id] = row
            except (OSError, csv.Error) as error:
                print(f"Advertencia: no se pudo leer metadata.csv: {error}")

        # 2) Discover PNG files on disk keyed by sample_id.
        png_sample_ids: dict[str, dict[str, str]] = {}
        png_pattern = re.compile(
            r"^([a-z_]+_\d{8}_\d{6}_\d{6}_\d{5})_(original|processed)_z[\dp]+\.png$"
        )
        for class_name in CLASSES:
            class_pattern = re.compile(
                rf"^({re.escape(class_name)}_\d{{8}}_\d{{6}}_\d{{6}}_(\d{{5}}))_"
            )
            for path in (self.root / class_name).glob("*.png"):
                match = png_pattern.match(path.name)
                if match:
                    sample_id = match.group(1)
                    png_sample_ids[sample_id] = {
                        "class": class_name,
                        "filename": (self.root / class_name / path.name)
                        .relative_to(self.root)
                        .as_posix(),
                    }
                else:
                    # Accept legacy filenames (no variant/zoom tag).
                    class_match = class_pattern.match(path.name)
                    if class_match:
                        sample_id = class_match.group(1)
                        png_sample_ids[sample_id] = {
                            "class": class_name,
                            "filename": (self.root / class_name / path.name)
                            .relative_to(self.root)
                            .as_posix(),
                        }

        # 3) Reconcile: remove CSV entries without PNGs on disk.
        valid_csv: dict[str, dict[str, str]] = {}
        orphaned_count = 0
        for sample_id, row in csv_rows.items():
            if sample_id in png_sample_ids:
                valid_csv[sample_id] = row
            else:
                orphaned_count += 1
        if orphaned_count > 0:
            print(
                f"Reconciliacion metadata: {orphaned_count} entrada(s) en metadata.csv "
                "sin PNG en disco (eliminadas)."
            )

        # 4) Reconcile: add PNG entries missing from CSV.
        added_count = 0
        for sample_id, info in png_sample_ids.items():
            if sample_id not in valid_csv:
                try:
                    sequence = int(sample_id.split("_")[-1])
                except ValueError:
                    sequence = 0
                valid_csv[sample_id] = {
                    "sample_id": sample_id,
                    "class": info["class"],
                    "captured_at": "",
                    "sequence": str(sequence),
                    "variant": "unknown",
                    "filename": info["filename"],
                    "zoom": "",
                    "zoom_applied": "",
                    "enhancement": "",
                    "source_width": "",
                    "source_height": "",
                    "source_sha256": "",
                    "difference_from_previous": "",
                    "esp32_url": "",
                }
                added_count += 1
        if added_count > 0:
            print(
                f"Reconciliacion metadata: {added_count} PNG(s) en disco "
                "sin entrada en metadata.csv (agregados)."
            )

        # 5) Rewrite metadata.csv with reconciled rows.
        if valid_csv or csv_rows:
            try:
                with self.metadata_path.open("w", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=METADATA_FIELDS)
                    writer.writeheader()
                    for row in valid_csv.values():
                        writer.writerow(row)
                    file.flush()
                    os.fsync(file.fileno())
            except (OSError, csv.Error) as error:
                print(f"Advertencia: no se pudo reescribir metadata.csv: {error}")

        # 6) Rebuild internal state from the reconciled metadata.
        for row in valid_csv.values():
            class_name = row.get("class", "")
            sample_id = row.get("sample_id", "")
            if class_name in CLASSES and sample_id:
                self._known_sample_ids.add(sample_id)
                try:
                    sequence = int(row.get("sequence", "0"))
                except ValueError:
                    sequence = 0
                self.next_sequences[class_name] = max(
                    self.next_sequences[class_name], sequence + 1
                )

        # 7) Final count from all known sample_ids.
        for sample_id in self._known_sample_ids:
            for class_name in CLASSES:
                if sample_id.startswith(f"{class_name}_"):
                    self.counts[class_name] += 1
                    break

    def save(
        self,
        capture: Capture,
        class_name: str,
        variants: Iterable[str],
        server_url: str,
    ) -> list[Path]:
        sequence = self.next_sequences[class_name]
        now = datetime.now().astimezone()
        timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
        sample_id = f"{class_name}_{timestamp}_{sequence:05d}"
        zoom_tag = f"z{capture.zoom:.2f}".replace(".", "p")
        selected = tuple(variants)
        written: list[Path] = []
        rows: list[dict[str, object]] = []

        for variant in selected:
            image = capture.original if variant == "original" else capture.processed
            filename = f"{sample_id}_{variant}_{zoom_tag}.png"
            destination = self.root / class_name / filename
            temporary = destination.with_name(f".{destination.stem}.tmp.png")
            if not cv2.imwrite(str(temporary), image):
                for path in written:
                    path.unlink(missing_ok=True)
                raise OSError(f"OpenCV no pudo escribir {destination}")
            temporary.replace(destination)
            written.append(destination)
            height, width = capture.original.shape[:2]
            rows.append(
                {
                    "sample_id": sample_id,
                    "class": class_name,
                    "captured_at": now.isoformat(timespec="milliseconds"),
                    "sequence": sequence,
                    "variant": variant,
                    "filename": destination.relative_to(self.root).as_posix(),
                    "zoom": f"{capture.zoom:.2f}",
                    "zoom_applied": variant == "processed" and capture.zoom != 1.0,
                    "enhancement": (
                        "none" if variant == "original" else "MEDIAN_3x3"
                    ),
                    "source_width": width,
                    "source_height": height,
                    "source_sha256": capture.source_sha256,
                    "difference_from_previous": (
                        ""
                        if capture.difference_from_previous is None
                        else f"{capture.difference_from_previous:.6f}"
                    ),
                    "esp32_url": server_url,
                }
            )

        try:
            new_file = (
                not self.metadata_path.exists()
                or self.metadata_path.stat().st_size == 0
            )
            with self.metadata_path.open("a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=METADATA_FIELDS)
                if new_file:
                    writer.writeheader()
                writer.writerows(rows)
                file.flush()
                os.fsync(file.fileno())
        except (OSError, csv.Error):
            for path in written:
                path.unlink(missing_ok=True)
            raise

        self._known_sample_ids.add(sample_id)
        self.next_sequences[class_name] += 1
        self.counts[class_name] += 1
        return written

    def print_counts(self) -> None:
        summary = " | ".join(
            f"{class_name}: {self.counts[class_name]}" for class_name in CLASSES
        )
        print(f"Capturas por clase: {summary}")


class CameraClient:
    def __init__(self, base_url: str, timeout: float, websocket_port: int) -> None:
        self.session = requests.Session()
        self.timeout = timeout
        self.websocket_port = websocket_port
        self.base_url = normalize_url(base_url)

    def set_base_url(self, base_url: str) -> None:
        self.base_url = normalize_url(base_url)

    @property
    def websocket_url(self) -> str:
        parsed = urlparse(self.base_url)
        host = parsed.hostname or parsed.path
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return f"{scheme}://{host}:{self.websocket_port}"

    def status(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=self.timeout)
            response.raise_for_status()
            status = response.json()
            print(
                "ESP32 conectado: "
                f"PID={status.get('sensor_pid', '?')}, "
                f"resolucion={status.get('resolution', '?')}, "
                f"RSSI={status.get('wifi_rssi', '?')} dBm, "
                f"heap={status.get('free_heap', '?')} bytes"
            )
            return True
        except (requests.RequestException, ValueError) as error:
            print(f"No se pudo consultar {self.base_url}/status: {error}")
            return False

    def capture(self) -> np.ndarray | None:
        try:
            response = self.session.get(
                f"{self.base_url}/capture", timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"Error de red durante la captura: {error}")
            return None

        content_type = response.headers.get("Content-Type", "").lower()
        if "image/bmp" not in content_type:
            print(f"Respuesta invalida: Content-Type={content_type!r}")
            return None

        return decode_bmp(response.content, "respuesta HTTP")


def normalize_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value.startswith(("http://", "https://")):
        value = f"http://{value}"
    return value


def decode_bmp(data: bytes, source: str) -> np.ndarray | None:
    encoded = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        print(f"OpenCV no pudo decodificar el BMP de {source} ({len(data)} bytes).")
        return None
    if image.shape[:2] != (FRAME_HEIGHT, FRAME_WIDTH):
        print(
            f"Frame invalido de {source}: se esperaba {FRAME_WIDTH}x{FRAME_HEIGHT} y llego "
            f"{image.shape[1]}x{image.shape[0]}."
        )
        return None
    return image


def decode_rgb565(data: bytes, source: str) -> np.ndarray | None:
    if len(data) != EXPECTED_RGB565_BYTES:
        print(
            f"Frame RGB565 invalido de {source}: "
            f"se esperaban {EXPECTED_RGB565_BYTES} bytes "
            f"y llegaron {len(data)}."
        )
        return None

    pixels = np.frombuffer(data, dtype=np.dtype(">u2"))
    pixels = pixels.reshape((FRAME_HEIGHT, FRAME_WIDTH))

    red_5 = (pixels >> 11) & 0x1F
    green_6 = (pixels >> 5) & 0x3F
    blue_5 = pixels & 0x1F

    red_8 = ((red_5 << 3) | (red_5 >> 2)).astype(np.uint8)
    green_8 = ((green_6 << 2) | (green_6 >> 4)).astype(np.uint8)
    blue_8 = ((blue_5 << 3) | (blue_5 >> 2)).astype(np.uint8)

    # OpenCV trabaja internamente en BGR.
    return np.dstack((blue_8, green_8, red_8))


def digital_zoom(image: np.ndarray, zoom: float) -> np.ndarray:
    if zoom == 1.0:
        return image.copy()
    height, width = image.shape[:2]
    crop_width = max(1, round(width / zoom))
    crop_height = max(1, round(height / zoom))
    left = (width - crop_width) // 2
    top = (height - crop_height) // 2
    crop = image[top : top + crop_height, left : left + crop_width]
    return cv2.resize(crop, (width, height), interpolation=cv2.INTER_CUBIC)


def denoise_image(image: np.ndarray) -> np.ndarray:
    return cv2.medianBlur(image, 3)


def normalized_difference(first: np.ndarray, second: np.ndarray) -> float:
    first_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    second_gray = cv2.cvtColor(second, cv2.COLOR_BGR2GRAY)
    if first_gray.shape != second_gray.shape:
        second_gray = cv2.resize(
            second_gray,
            (first_gray.shape[1], first_gray.shape[0]),
            interpolation=cv2.INTER_AREA,
        )
    return float(cv2.absdiff(first_gray, second_gray).mean() / 255.0)


def add_preview_label(image: np.ndarray, lines: Iterable[str]) -> np.ndarray:
    scale = 3
    preview = cv2.resize(
        image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST
    )
    y = 22
    for line in lines:
        cv2.putText(
            preview,
            line,
            (8, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            preview,
            line,
            (8, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        y += 20
    return preview


async def review_capture(capture: Capture, class_name: str, duplicate: bool) -> str:
    original_preview = add_preview_label(
        capture.original, (f"ORIGINAL | clase: {class_name}", "Sin zoom ni realce")
    )
    processed_preview = add_preview_label(
        capture.processed,
        (
            f"PROCESADA | zoom: {capture.zoom:.2f}x",
            "Filtro mediano 3x3",
        ),
    )
    cv2.imshow("Original recibida", original_preview)
    cv2.imshow("Zoom + filtro mediano", processed_preview)

    if duplicate:
        print(
            "Captura casi identica a la ultima guardada. O/P/B estan bloqueadas; use F para autorizar."
        )
    print(
        "Revision: [O] original  [P/A] procesada  [B] ambas  [D] descartar  [R] repetir  [F] forzar duplicado"
    )
    duplicate_blocked = duplicate
    while True:
        key = cv2.waitKey(20) & 0xFF
        await asyncio.sleep(0.01)
        if key in (ord("d"), ord("D"), 27):
            return "discard"
        if key in (ord("r"), ord("R")):
            return "repeat"
        if key in (ord("f"), ord("F")) and duplicate_blocked:
            duplicate_blocked = False
            print("Guardado habilitado para esta captura. Elija O, P/A o B.")
            continue
        if duplicate_blocked and key in (
            ord("o"),
            ord("O"),
            ord("p"),
            ord("P"),
            ord("a"),
            ord("A"),
            ord("b"),
            ord("B"),
        ):
            print("Posible duplicado: presione F primero, o D/R.")
            continue
        if key in (ord("o"), ord("O")):
            return "original"
        if key in (ord("p"), ord("P"), ord("a"), ord("A")):
            return "processed"
        if key in (ord("b"), ord("B")):
            return "both"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Previsualiza y captura un dataset desde ESP32-CAM por WebSocket."
    )
    parser.add_argument("--ip", help="IP o URL del ESP32-CAM, por ejemplo 192.168.1.50")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).resolve().parent / "dataset",
        help="Carpeta raiz del dataset (por defecto: project/dataset)",
    )
    parser.add_argument(
        "--timeout", type=float, default=12.0, help="Timeout HTTP en segundos"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=2,
        help="FPS solicitados al ESP32 (1-4)",
    )
    parser.add_argument(
        "--ws-port", type=int, default=81, help="Puerto WebSocket del ESP32"
    )
    parser.add_argument(
        "--duplicate-threshold",
        type=float,
        default=0.012,
        help="Diferencia media normalizada por debajo de la cual se advierte duplicado",
    )
    return parser.parse_args()


async def run_stream(
    camera: CameraClient,
    dataset: DatasetManager,
    state: StreamState,
    fps: int,
    duplicate_threshold: float,
) -> str:
    print(f"Conectando al stream {camera.websocket_url} ...")
    async with websockets.connect(
        camera.websocket_url,
        open_timeout=camera.timeout,
        ping_interval=20,
        ping_timeout=20,
        max_size=512 * 1024,
        max_queue=2,
    ) as websocket:
        await websocket.send(f"FPS:{fps}")
        await websocket.send("START")
        print("Stream conectado.")
        print(
            "[1-3] clase  [Z] zoom  [C] capturar  [S] estado  [I] cambiar IP  [Q] salir"
        )

        receive_task = asyncio.create_task(websocket.recv())
        latest_original: np.ndarray | None = None
        latest_processed: np.ndarray | None = None
        measured_fps = 0.0
        previous_frame_at: float | None = None

        try:
            while True:
                done, _ = await asyncio.wait({receive_task}, timeout=0.02)
                if receive_task in done:
                    message = receive_task.result()
                    receive_task = asyncio.create_task(websocket.recv())
                    if isinstance(message, bytes):
                        decoded = decode_rgb565(message, "stream WebSocket")
                        if decoded is not None:
                            latest_original = decoded
                            zoom = ZOOM_LEVELS[state.zoom_index]
                            latest_processed = denoise_image(
                                digital_zoom(decoded, zoom)
                            )
                            now = time.monotonic()
                            if previous_frame_at is not None:
                                instantaneous = 1.0 / max(now - previous_frame_at, 1e-6)
                                measured_fps = (
                                    instantaneous
                                    if measured_fps == 0.0
                                    else measured_fps * 0.8 + instantaneous * 0.2
                                )
                            previous_frame_at = now
                            class_name = CLASSES[state.class_index]
                            original_preview = add_preview_label(
                                latest_original,
                                (
                                    f"EN VIVO | clase: {class_name}",
                                    f"Original {FRAME_WIDTH}x{FRAME_HEIGHT} | {measured_fps:.1f} FPS",
                                    "C capturar | 1-3 clase | Z zoom | Q salir",
                                ),
                            )
                            processed_preview = add_preview_label(
                                latest_processed,
                                (
                                    f"EN VIVO PROCESADA | zoom: {zoom:.2f}x",
                                    "Filtro mediano 3x3",
                                ),
                            )
                            cv2.imshow("Original recibida", original_preview)
                            cv2.imshow("Zoom + filtro mediano", processed_preview)
                    elif message.startswith("ERROR:"):
                        print(f"ESP32 WebSocket: {message}")

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):
                    await websocket.send("STOP")
                    return "quit"
                if key in (ord("i"), ord("I")):
                    await websocket.send("STOP")
                    return "change_ip"
                if key in (ord("s"), ord("S")):
                    await asyncio.to_thread(camera.status)
                    continue
                if key in (ord("1"), ord("2"), ord("3")):
                    state.class_index = int(chr(key)) - 1
                    print(f"Clase seleccionada: {CLASSES[state.class_index]}")
                    dataset.print_counts()
                    continue
                if key in (ord("z"), ord("Z")):
                    state.zoom_index = (state.zoom_index + 1) % len(ZOOM_LEVELS)
                    print(f"Zoom seleccionado: {ZOOM_LEVELS[state.zoom_index]:.2f}x")
                    continue
                if key not in (ord("c"), ord("C")):
                    continue
                if latest_original is None or latest_processed is None:
                    print("Todavia no se recibio un frame valido.")
                    continue

                await websocket.send("PAUSE")
                original = latest_original.copy()
                zoom = ZOOM_LEVELS[state.zoom_index]
                processed = denoise_image(digital_zoom(original, zoom))
                difference = (
                    None
                    if state.last_saved_original is None
                    else normalized_difference(state.last_saved_original, original)
                )
                duplicate = difference is not None and difference < duplicate_threshold
                capture = Capture(
                    original=original,
                    processed=processed,
                    zoom=zoom,
                    source_sha256=hashlib.sha256(original.tobytes()).hexdigest(),
                    difference_from_previous=difference,
                )
                if difference is not None:
                    print(
                        f"Diferencia respecto de la ultima captura guardada: {difference:.4f}"
                    )

                action = await review_capture(
                    capture, CLASSES[state.class_index], duplicate
                )
                if action == "discard":
                    print("Captura descartada.")
                elif action != "repeat":
                    variants = (
                        ("original", "processed") if action == "both" else (action,)
                    )
                    try:
                        paths = dataset.save(
                            capture,
                            CLASSES[state.class_index],
                            variants,
                            camera.base_url,
                        )
                    except (OSError, csv.Error) as error:
                        print(f"No se pudo guardar la captura: {error}")
                    else:
                        state.last_saved_original = original.copy()
                        print("Guardado: " + ", ".join(str(path) for path in paths))
                        dataset.print_counts()
                await websocket.send("START")
        finally:
            receive_task.cancel()
            await asyncio.gather(receive_task, return_exceptions=True)


async def async_main(args: argparse.Namespace) -> int:
    address = args.ip or await asyncio.to_thread(input, "IP del ESP32-CAM: ")
    address = address.strip()
    if not address:
        print("Debe indicar una direccion IP.")
        return 2

    dataset = DatasetManager(args.dataset.expanduser().resolve())
    camera = CameraClient(address, args.timeout, args.ws_port)
    state = StreamState()
    print(f"Dataset: {dataset.root}")
    await asyncio.to_thread(camera.status)
    dataset.print_counts()

    try:
        while True:
            try:
                result = await run_stream(
                    camera, dataset, state, args.fps, args.duplicate_threshold
                )
            except (OSError, WebSocketException, asyncio.TimeoutError) as error:
                print(f"Conexion WebSocket perdida: {error}")
                print("Reintentando en 2 segundos. Presione Ctrl+C para salir.")
                await asyncio.sleep(2)
                continue

            if result == "quit":
                break
            if result == "change_ip":
                new_address = await asyncio.to_thread(
                    input, f"Nueva IP o URL [{camera.base_url}]: "
                )
                if new_address.strip():
                    camera.set_base_url(new_address)
                    await asyncio.to_thread(camera.status)
    except (KeyboardInterrupt, EOFError):
        print("\nCaptura interrumpida por el usuario.")
    finally:
        cv2.destroyAllWindows()
        camera.session.close()

    print("Programa finalizado sin perder las capturas guardadas.")
    return 0


def main() -> int:
    args = parse_args()
    if (
        args.timeout <= 0
        or not 0 <= args.duplicate_threshold <= 1
        or not 1 <= args.fps <= 4
        or not 1 <= args.ws_port <= 65535
    ):
        print("Revise: timeout > 0, umbral 0-1, FPS 1-4 y puerto 1-65535.")
        return 2
    try:
        return asyncio.run(async_main(args))
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        print("\nCaptura interrumpida por el usuario.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
