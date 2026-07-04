# Encender un led del color que muestre la cámara.
# Ejercicio 1, Módulo II

from numpy import square
import serial
import time
import cv2
import numpy as np

PUERTO_SERIAL = (
    "/dev/ttyACM0"  # puerto que sale cuando
    # se enchufa el arduino mega o la placa
)
BAUDRATE = 9600  # default en la mayoría de las veces
UMBRAL_NEGRO = 70
AREA_MINIMA_CUADRADO = 4000
KERNEL_MORFOLOGICO = np.ones((5, 5), np.uint8)


arduino = serial.Serial(
    PUERTO_SERIAL, BAUDRATE, timeout=1
)  # representación del dispositivo, el serial monitor debe estar cerrado
time.sleep(2)

camara = cv2.VideoCapture(0)  # solo tengo una cam, así que ponemos índice 0

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
            if area < AREA_MINIMA_CUADRADO:
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
    if resultado is not None:
        cuadrado_encontrado, interior_encontrado = resultado
        cv2.drawContours(frame, [cuadrado_encontrado], -1, (0, 255, 0), 2)
        # cuadro,
        # texto a poner, posicion, fuente de texto, grosor, tupla bgr, etc.
        """
        cv2.putText(
            frame,
            "Cuadrado detectado",
            (10, 30),
            cv2.FONT_HERSHEY_COMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
        """

        x, y, w, h = cv2.boundingRect(interior_encontrado)
        roi = frame[y : y + h, x : x + w]

        if roi.size > 0:
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            mascara_color = cv2.inRange(hsv, (0, 80, 40), (180, 255, 255))

            # para eliminar ruido de sal y pimiento, se hace open y close
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
                    cv2.drawContours(roi, [mejor_circulo], -1, (0, 0, 255), 2)

                cv2.imshow("ROI", roi)
                cv2.imshow("Mascara color", mascara_color)

    cv2.imshow("Camara", frame)  # NO PONER TILDES EN LA CAM
    cv2.imshow("Binarizacion", binaria)  # NO PONER TILDES EN LA CAM

    # time.sleep(1)
    # el 0xFF es un salto de línea. si es la tecla q, se sale del programa.

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    # Destruir la imagen, va a tener problemas

camara.release()
cv2.destroyAllWindows()
