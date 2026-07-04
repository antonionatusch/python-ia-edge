# Encender un led del color que muestre la cámara.
# Ejercicio 1, Módulo II

from numpy import square
import serial
import time
import cv2

PUERTO_SERIAL = (
    "/dev/ttyACM0"  # puerto que sale cuando
    # se enchufa el arduino mega o la placa
)
BAUDRATE = 9600  # default en la mayoría de las veces
UMBRAL_NEGRO = 70
AREA_MINIMA_CUADRADO = 4000


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
    cuadrado_encontrado = None
    interior_encontado = None

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

            cuadrado_encontrado = aprox  # devuelve contorno identificado
            interior_encontado = contornos[hijo]
            break

    # nota: el tree puede usarse, pero en este caso, solo vemos si tiene
    # contorno interno y externo
    # ccomp da cierta jerarquía pero no tanta

    # identificado el contorno con la jerarquía

    # -1 es para graficar todos los contornos, lo marco de verde
    # la tupla es orden BGR
    # el 2 indica el ancho de la linea para el contorno
    if cuadrado_encontrado is not None:
        cv2.drawContours(frame, [cuadrado_encontrado], -1, (0, 255, 0), 2)
        # cuadro,
        # texto a poner, posicion, fuente de texto, grosor, tupla bgr, etc.
        cv2.putText(
            frame,
            "Cuadrado detectado",
            (10, 30),
            cv2.FONT_HERSHEY_COMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

    cv2.imshow("Camara", frame)  # NO PONER TILDES EN LA CAM
    cv2.imshow("Binarizacion", binaria)  # NO PONER TILDES EN LA CAM

    # el 0xFF es un salto de línea. si es la tecla q, se sale del programa.

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    # Destruir la imagen, va a tener problemas

camara.release()
cv2.destroyAllWindows()
