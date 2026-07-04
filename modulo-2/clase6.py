import serial
import time

PUERTO_SERIAL = (
    "/dev/ttyACM0"  # puerto que sale cuando se enchufa el arduino mega o la placa
)
BAUDRATE = 9600  # default en la mayoría de las veces

arduino = serial.Serial(
    PUERTO_SERIAL, BAUDRATE, timeout=1
)  # representación del dispositivo, el serial monitor debe estar cerrado
time.sleep(2)

while True:
    arduino.write("hola\n".encode())
    print("Python envió: hola")

    respuesta = arduino.readline().decode().strip()
    if respuesta:
        print(f"Arduino respondió: {respuesta}")
        break

    time.sleep(1)
