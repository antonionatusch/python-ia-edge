# Encender un led del color que muestre la cámara.
# Mini Ejercicio 2, Módulo II

import time
import cv2
import numpy as np
import websockets
import asyncio

IP_ESP32 = "192.168.0.21"
ESP32_WS_URL = f"ws://{IP_ESP32}:81"
UMBRAL_NEGRO = 70
AREA_MINIMA_CUADRO = 4000
TAMANO_BUFFER = 8
KERNEL_MORFOLOGICO = np.ones((5, 5), np.uint8)

COLOR_BGR = {"R": (0, 0, 255), "G": (0, 255, 0), "B": (255, 0, 0), "N": (200, 200, 200)}

TEXTO_COLOR = {"R": "ROJO", "G": "VERDE", "B": "AZUL", "N": "NINGUNO"}

RANGO_ROJO_1 = ((0, 100, 70), (10, 255, 255))
RANGO_ROJO_2 = ((170, 100, 70), (180, 255, 255))
RANGO_VERDE = ((40, 70, 60), (85, 255, 255))
RANGO_AZUL = ((90, 50, 40), (135, 255, 255))


async def main():
    async with websockets.connect(ESP32_WS_URL) as ws:
        print("[WebSocket] Conectado a ESP32")

        camara = cv2.VideoCapture(0)  # solo tengo una cam, así que ponemos índice 0
        buffer_colores = []
        buffer_fps = []
        TAMANO_BUFFER_FPS = 15
        ultimo_color_enviado = None
        tiempo_anterior = time.time()

        while True:

            ok, frame = camara.read()
            if not ok:
                break

            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, binaria = cv2.threshold(gris, UMBRAL_NEGRO, 255, cv2.THRESH_BINARY)

            contornos, jerarquia = cv2.findContours(
                binaria, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
            )
            resultado = None

            if jerarquia is not None:
                for i, contorno in enumerate(contornos):
                    area = cv2.contourArea(contorno)
                    if area < AREA_MINIMA_CUADRO:
                        continue

                    perimetro = cv2.arcLength(contorno, True)
                    # el 3% es porque depende de la impresión
                    aprox = cv2.approxPolyDP(contorno, 0.03 * perimetro, True)
                    # ver si es un cuadrado
                    square_sides = 4
                    if len(aprox) != square_sides:
                        continue

                    # ver si tiene contorno interno
                    # jerarquita[i] =
                    # [siguiente contorno, anterior contorno, primer hijo, padre]
                    hijo = jerarquia[0][i][2]

                    # analizando el hijo
                    if hijo == -1:
                        continue

                    resultado = (aprox, contornos[hijo])
                    break

            # nota: el tree puede usarse, pero en este caso, solo vemos si tiene
            # contorno interno y externo
            # ccomp da cierta jerarquía pero no tanta

            # identificado el contorno con la jerarquía

            # -1 es para graficar todos los contornos, lo marco de verde
            # la tupla es orden BGR
            # el 2 indica el ancho de la linea para el contorno

            color_detectado = "N"

            if resultado is not None:
                cuadrado_encontrado, interior_encontrado = resultado
                cv2.drawContours(frame, [cuadrado_encontrado], -1, (0, 255, 0), 2)

                x, y, w, h = cv2.boundingRect(interior_encontrado)
                roi = frame[y : y + h, x : x + w]

                if roi.size > 0:
                    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

                    mascara_color = cv2.inRange(hsv, (0, 80, 40), (180, 255, 255))

                    # para eliminar ruido de sal y pimienta, se hace open y close
                    mascara_color = cv2.morphologyEx(
                        mascara_color, cv2.MORPH_OPEN, KERNEL_MORFOLOGICO
                    )

                    mascara_color = cv2.morphologyEx(
                        mascara_color, cv2.MORPH_CLOSE, KERNEL_MORFOLOGICO
                    )

                    contornos_circulo, _ = cv2.findContours(
                        mascara_color, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                    )

                    mejor_circulo = None
                    mejor_circularidad = 0

                    for contorno in contornos_circulo:
                        area_c = cv2.contourArea(contorno)
                        if area_c < 150:
                            continue

                        perimetro_c = cv2.arcLength(contorno, True)

                        if perimetro_c == 0:
                            continue

                        # analizando circularidad, perimetro del circulo

                        circularidad = 4 * np.pi * (area_c / (perimetro_c**2))

                        if circularidad > mejor_circularidad:
                            mejor_circularidad = circularidad
                            mejor_circulo = contorno

                        if mejor_circulo is not None and mejor_circularidad > 0.7:
                            mascara_circulo = np.zeros(hsv.shape[:2], dtype=np.uint8)
                            cv2.drawContours(
                                mascara_circulo, [mejor_circulo], -1, 255, -1
                            )

                            mascara_r_c = cv2.bitwise_and(
                                cv2.inRange(hsv, RANGO_ROJO_1[0], RANGO_ROJO_1[1])
                                | cv2.inRange(hsv, RANGO_ROJO_2[0], RANGO_ROJO_2[1]),
                                mascara_circulo,
                            )
                            mascara_g_c = cv2.bitwise_and(
                                cv2.inRange(hsv, RANGO_VERDE[0], RANGO_VERDE[1]),
                                mascara_circulo,
                            )
                            mascara_b_c = cv2.bitwise_and(
                                cv2.inRange(hsv, RANGO_AZUL[0], RANGO_AZUL[1]),
                                mascara_circulo,
                            )

                            conteos = {
                                "R": cv2.countNonZero(mascara_r_c),
                                "G": cv2.countNonZero(mascara_g_c),
                                "B": cv2.countNonZero(mascara_b_c),
                            }
                            color_ganador, conteo_ganador = max(
                                conteos.items(), key=lambda kv: kv[1]
                            )
                            area_circulo = cv2.countNonZero(mascara_circulo)

                            if area_circulo > 0 and conteo_ganador > 0.3 * area_circulo:
                                color_detectado = color_ganador

                        cv2.imshow("ROI", roi)
                        cv2.imshow("Mascara color", mascara_color)

            buffer_colores.append(color_detectado)
            if len(buffer_colores) > TAMANO_BUFFER:
                buffer_colores.pop(0)

            color_estable = max(set(buffer_colores), key=buffer_colores.count)

            if color_estable != ultimo_color_enviado:
                ultimo_color_enviado = color_estable
                await ws.send(color_estable)
                print(f"Color enviado: {color_estable}")

            tiempo_actual = time.time()
            fps_instantaneo = 1.0 / max(tiempo_actual - tiempo_anterior, 1e-6)
            tiempo_anterior = tiempo_actual

            buffer_fps.append(fps_instantaneo)
            if len(buffer_fps) > TAMANO_BUFFER_FPS:
                buffer_fps.pop(0)
            fps = sum(buffer_fps) / len(buffer_fps)

            cv2.putText(
                frame,
                f"Color: {TEXTO_COLOR[color_estable]}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                COLOR_BGR[color_estable],
                2,
            )
            cv2.putText(
                frame,
                f"Enviado por WebSocket: {color_estable}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                COLOR_BGR[color_estable],
                2,
            )
            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            mascara_r = cv2.inRange(
                hsv_frame, RANGO_ROJO_1[0], RANGO_ROJO_1[1]
            ) | cv2.inRange(hsv_frame, RANGO_ROJO_2[0], RANGO_ROJO_2[1])
            mascara_g = cv2.inRange(hsv_frame, RANGO_VERDE[0], RANGO_VERDE[1])
            mascara_b = cv2.inRange(hsv_frame, RANGO_AZUL[0], RANGO_AZUL[1])

            mascara_r = cv2.morphologyEx(mascara_r, cv2.MORPH_OPEN, KERNEL_MORFOLOGICO)
            mascara_g = cv2.morphologyEx(mascara_g, cv2.MORPH_OPEN, KERNEL_MORFOLOGICO)
            mascara_b = cv2.morphologyEx(mascara_b, cv2.MORPH_OPEN, KERNEL_MORFOLOGICO)

            salida_r = np.zeros_like(frame)
            salida_r[:, :, 2] = mascara_r

            salida_g = np.zeros_like(frame)
            salida_g[:, :, 1] = mascara_g

            salida_b = np.zeros_like(frame)
            salida_b[:, :, 0] = mascara_b

            cv2.imshow("Mascara ROJO", salida_r)
            cv2.imshow("Mascara VERDE", salida_g)
            cv2.imshow("Mascara AZUL", salida_b)

            cv2.imshow("Camara", frame)  # NO PONER TILDES EN LA CAM
            cv2.imshow("Binarizacion", binaria)  # NO PONER TILDES EN LA CAM

            # el 0xFF es un salto de línea. si es la tecla q, se sale del programa.

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        camara.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
