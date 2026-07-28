from pathlib import Path

import numpy as np
import requests
from PIL import Image

ESP32_CAPTURE_URL = "http://192.168.0.3/capture"
OUTPUT_PATH = Path("captura.png")

EXPECTED_WIDTH = 320
EXPECTED_HEIGHT = 240
BYTES_PER_PIXEL = 2

# El GC2145 normalmente entrega primero el byte más significativo.
# Si los colores salen incorrectos, cambia "big" por "little".
BYTE_ORDER = "big"


def download_frame(url: str) -> tuple[bytes, int, int]:
    print(f"[HTTP] Solicitando captura a {url}...")

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    width = int(response.headers.get("X-Image-Width", EXPECTED_WIDTH))
    height = int(response.headers.get("X-Image-Height", EXPECTED_HEIGHT))
    pixel_format = response.headers.get("X-Pixel-Format", "desconocido")

    frame_data = response.content
    expected_size = width * height * BYTES_PER_PIXEL

    print(f"[HTTP] Estado: {response.status_code}")
    print(f"[IMAGEN] Dimensiones: {width} × {height}")
    print(f"[IMAGEN] Formato: {pixel_format}")
    print(f"[IMAGEN] Bytes recibidos: {len(frame_data)}")
    print(f"[IMAGEN] Bytes esperados: {expected_size}")

    if pixel_format.upper() != "RGB565":
        raise ValueError(f"Se esperaba RGB565, pero el servidor indicó {pixel_format}.")

    if len(frame_data) != expected_size:
        raise ValueError(
            "La captura está incompleta o tiene dimensiones inesperadas: "
            f"se recibieron {len(frame_data)} de {expected_size} bytes."
        )

    return frame_data, width, height


def rgb565_to_rgb888(
    frame_data: bytes,
    width: int,
    height: int,
    byte_order: str = "big",
) -> np.ndarray:
    if byte_order == "big":
        dtype = np.dtype(">u2")
    elif byte_order == "little":
        dtype = np.dtype("<u2")
    else:
        raise ValueError("byte_order debe ser 'big' o 'little'.")

    pixels = np.frombuffer(frame_data, dtype=dtype)
    pixels = pixels.reshape((height, width))

    # RGB565:
    # RRRRR GGGGGG BBBBB
    red_5 = (pixels >> 11) & 0x1F
    green_6 = (pixels >> 5) & 0x3F
    blue_5 = pixels & 0x1F

    # Expandir:
    # rojo y azul: 5 bits → 8 bits
    # verde:       6 bits → 8 bits
    red_8 = ((red_5 << 3) | (red_5 >> 2)).astype(np.uint8)
    green_8 = ((green_6 << 2) | (green_6 >> 4)).astype(np.uint8)
    blue_8 = ((blue_5 << 3) | (blue_5 >> 2)).astype(np.uint8)

    return np.dstack((red_8, green_8, blue_8))


def main() -> None:
    try:
        frame_data, width, height = download_frame(ESP32_CAPTURE_URL)

        rgb_image = rgb565_to_rgb888(
            frame_data,
            width,
            height,
            BYTE_ORDER,
        )

        image = Image.fromarray(rgb_image, mode="RGB")
        image.save(OUTPUT_PATH)

        print(f"[OK] Imagen guardada en: {OUTPUT_PATH.resolve()}")

        # Abre la imagen con el visor predeterminado del sistema.
        image.show()

    except requests.ConnectionError:
        print(
            "[ERROR] No fue posible conectar con la ESP32-CAM. "
            "Comprueba la IP y que ambos equipos estén en la misma red."
        )

    except requests.Timeout:
        print("[ERROR] La ESP32-CAM tardó demasiado en responder.")

    except requests.HTTPError as error:
        print(f"[ERROR] El servidor devolvió un error HTTP: {error}")

    except ValueError as error:
        print(f"[ERROR] Captura inválida: {error}")

    except Exception as error:
        print(f"[ERROR] Error inesperado: {error}")


if __name__ == "__main__":
    main()
