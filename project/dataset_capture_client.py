#!/usr/bin/env python3
"""Interactive HTTP dataset collector for the ESP32-CAM GC2145 server."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
import requests


CLASSES = ("empty", "half_full", "full", "obstructed")
ZOOM_LEVELS = (1.0, 1.25, 1.5, 2.0)
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

        if self.metadata_path.exists():
            try:
                with self.metadata_path.open("r", newline="", encoding="utf-8") as file:
                    for row in csv.DictReader(file):
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
            except (OSError, csv.Error) as error:
                print(f"Advertencia: no se pudo leer metadata.csv: {error}")

        # Also discover PNG files if metadata was removed or is incomplete.
        for class_name in CLASSES:
            pattern = re.compile(
                rf"^({re.escape(class_name)}_\d{{8}}_\d{{12}}_(\d{{5}}))_"
            )
            for path in (self.root / class_name).glob("*.png"):
                match = pattern.match(path.name)
                if match:
                    self._known_sample_ids.add(match.group(1))
                    self.next_sequences[class_name] = max(
                        self.next_sequences[class_name], int(match.group(2)) + 1
                    )

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
                    "enhancement": "none" if variant == "original" else "CLAHE_L_1.5_8x8",
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
            new_file = not self.metadata_path.exists() or self.metadata_path.stat().st_size == 0
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
    def __init__(self, base_url: str, timeout: float) -> None:
        self.session = requests.Session()
        self.timeout = timeout
        self.base_url = normalize_url(base_url)

    def set_base_url(self, base_url: str) -> None:
        self.base_url = normalize_url(base_url)

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
            response = self.session.get(f"{self.base_url}/capture", timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"Error de red durante la captura: {error}")
            return None

        content_type = response.headers.get("Content-Type", "").lower()
        if "image/bmp" not in content_type:
            print(f"Respuesta invalida: Content-Type={content_type!r}")
            return None

        encoded = np.frombuffer(response.content, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            print(f"OpenCV no pudo decodificar el BMP de {len(response.content)} bytes.")
            return None
        if image.shape[:2] != (120, 160):
            print(f"Captura invalida: se esperaba 160x120 y llego {image.shape[1]}x{image.shape[0]}.")
            return None
        return image


def normalize_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value.startswith(("http://", "https://")):
        value = f"http://{value}"
    return value


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


def enhance_luminance(image: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    luminance, channel_a, channel_b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    enhanced = cv2.merge((clahe.apply(luminance), channel_a, channel_b))
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def normalized_difference(first: np.ndarray, second: np.ndarray) -> float:
    first_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    second_gray = cv2.cvtColor(second, cv2.COLOR_BGR2GRAY)
    if first_gray.shape != second_gray.shape:
        second_gray = cv2.resize(
            second_gray, (first_gray.shape[1], first_gray.shape[0]), interpolation=cv2.INTER_AREA
        )
    return float(cv2.absdiff(first_gray, second_gray).mean() / 255.0)


def add_preview_label(image: np.ndarray, lines: Iterable[str]) -> np.ndarray:
    scale = 3
    preview = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
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


def review_capture(capture: Capture, class_name: str, duplicate: bool) -> str:
    original_preview = add_preview_label(
        capture.original, (f"ORIGINAL | clase: {class_name}", "Sin zoom ni realce")
    )
    processed_preview = add_preview_label(
        capture.processed,
        (f"PROCESADA | zoom: {capture.zoom:.2f}x", "CLAHE suave en luminancia"),
    )
    cv2.imshow("Original recibida", original_preview)
    cv2.imshow("Zoom + realce CLAHE", processed_preview)

    if duplicate:
        print("Captura casi identica a la ultima guardada. O/P/B estan bloqueadas; use F para autorizar.")
    print("Revision: [O] original  [P/A] procesada  [B] ambas  [D] descartar  [R] repetir  [F] forzar duplicado")
    duplicate_blocked = duplicate
    while True:
        key = cv2.waitKey(0) & 0xFF
        if key in (ord("d"), ord("D"), 27):
            return "discard"
        if key in (ord("r"), ord("R")):
            return "repeat"
        if key in (ord("f"), ord("F")) and duplicate_blocked:
            duplicate_blocked = False
            print("Guardado habilitado para esta captura. Elija O, P/A o B.")
            continue
        if duplicate_blocked and key in (ord("o"), ord("O"), ord("p"), ord("P"), ord("a"), ord("A"), ord("b"), ord("B")):
            print("Posible duplicado: presione F primero, o D/R.")
            continue
        if key in (ord("o"), ord("O")):
            return "original"
        if key in (ord("p"), ord("P"), ord("a"), ord("A")):
            return "processed"
        if key in (ord("b"), ord("B")):
            return "both"


def select_zoom(current: float) -> float:
    print("Zoom disponible: " + " | ".join(f"{index + 1}: {zoom:.2f}x" for index, zoom in enumerate(ZOOM_LEVELS)))
    choice = input(f"Zoom [{current:.2f}x]: ").strip()
    if not choice:
        return current
    try:
        return ZOOM_LEVELS[int(choice) - 1]
    except (ValueError, IndexError):
        print("Nivel de zoom invalido; se conserva el valor actual.")
        return current


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Captura un dataset desde ESP32-CAM por HTTP.")
    parser.add_argument("--ip", help="IP o URL del ESP32-CAM, por ejemplo 192.168.1.50")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).resolve().parent / "dataset",
        help="Carpeta raiz del dataset (por defecto: project/dataset)",
    )
    parser.add_argument("--timeout", type=float, default=12.0, help="Timeout HTTP en segundos")
    parser.add_argument(
        "--duplicate-threshold",
        type=float,
        default=0.012,
        help="Diferencia media normalizada por debajo de la cual se advierte duplicado",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.timeout <= 0 or not 0 <= args.duplicate_threshold <= 1:
        print("--timeout debe ser positivo y --duplicate-threshold debe estar entre 0 y 1.")
        return 2

    address = args.ip or input("IP del ESP32-CAM: ").strip()
    if not address:
        print("Debe indicar una direccion IP.")
        return 2

    dataset = DatasetManager(args.dataset.expanduser().resolve())
    camera = CameraClient(address, args.timeout)
    current_class = CLASSES[0]
    current_zoom = ZOOM_LEVELS[0]
    last_saved_original: np.ndarray | None = None

    print(f"Dataset: {dataset.root}")
    camera.status()

    try:
        while True:
            print(f"\nClase: {current_class} | zoom procesado: {current_zoom:.2f}x")
            dataset.print_counts()
            print("[1] empty  [2] half_full  [3] full  [4] obstructed")
            print("[C] capturar  [Z] cambiar zoom  [I] cambiar IP  [S] estado  [Q] salir")
            choice = input("> ").strip().lower()

            if choice in {"1", "2", "3", "4"}:
                current_class = CLASSES[int(choice) - 1]
                continue
            if choice == "z":
                current_zoom = select_zoom(current_zoom)
                continue
            if choice == "i":
                new_address = input(f"Nueva IP o URL [{camera.base_url}]: ").strip()
                if new_address:
                    camera.set_base_url(new_address)
                    camera.status()
                continue
            if choice == "s":
                camera.status()
                continue
            if choice == "q":
                break
            if choice != "c":
                print("Opcion no reconocida.")
                continue

            while True:
                print("Solicitando captura...")
                original = camera.capture()
                if original is None:
                    retry = input("La captura fallo. [R] reintentar o [M] menu: ").strip().lower()
                    if retry == "r":
                        continue
                    break

                difference = (
                    None
                    if last_saved_original is None
                    else normalized_difference(last_saved_original, original)
                )
                duplicate = difference is not None and difference < args.duplicate_threshold
                zoomed = digital_zoom(original, current_zoom)
                processed = enhance_luminance(zoomed)
                capture = Capture(
                    original=original,
                    processed=processed,
                    zoom=current_zoom,
                    source_sha256=hashlib.sha256(original.tobytes()).hexdigest(),
                    difference_from_previous=difference,
                )
                if difference is not None:
                    print(f"Diferencia respecto de la ultima captura guardada: {difference:.4f}")

                action = review_capture(capture, current_class, duplicate)
                cv2.destroyAllWindows()
                cv2.waitKey(1)
                if action == "repeat":
                    continue
                if action == "discard":
                    print("Captura descartada.")
                    break

                variants = ("original", "processed") if action == "both" else (action,)
                try:
                    paths = dataset.save(capture, current_class, variants, camera.base_url)
                except (OSError, csv.Error) as error:
                    print(f"No se pudo guardar la captura: {error}")
                    retry = input("[R] intentar otra captura o [M] menu: ").strip().lower()
                    if retry == "r":
                        continue
                    break

                last_saved_original = original.copy()
                print("Guardado: " + ", ".join(str(path) for path in paths))
                dataset.print_counts()
                break
    except (KeyboardInterrupt, EOFError):
        print("\nCaptura interrumpida por el usuario.")
    finally:
        cv2.destroyAllWindows()
        camera.session.close()

    print("Programa finalizado sin perder las capturas guardadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
