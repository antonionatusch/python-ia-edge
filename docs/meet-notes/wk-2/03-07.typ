#set text(lang: "es")

#align(center)[
  = Comienzo del módulo 2
  = 03/07/2026
  == Uniendo hardware con software
]

= Conceptos previos
Es necesario saber qué es una imagen, sus características,
etc.

Hay que hablar de la captura, efecto Doppler, etc.

#figure(
  image("assets/images/about-processing.png", width: 80%),
  caption: [Sobre el procesamiento en bajo, medio y alto nivel],
) <fig-about-processing>

#linebreak()

#figure(
  image("assets/images/about-python-elecboard-plc.png", width: 80%),
  caption: [Sobre el pipeline desde OpenCV hasta un componente PLC],
) <fig-about-python-elecboard-plc>

= Sobre la comunicación serial

#figure(
  image("assets/images/about-serial-comms.png", width: 80%),
) <fig-about-serial-comms>

Existe comunicación asíncrona y síncrona.
En la asíncrona, no necesariamente depende del reloj,
mientras que en la síncrona sí.


== Tipos
=== UART


#figure(
  image("assets/images/about-uart.png", width: 80%),
  caption: [Sobre protocolo UART],
) <fig-about-uart>

==== Sobre las características
- Full dúplex: No tiene cuello de botella; puede
  tanto enviar como recibir información al mismo
  tiempo sin tener que esperar.

El ejemplo de la figura es de los que más se utiliza en proyectos reales.

==== Datos de UART

#figure(
  image("assets/images/uart-info-1.png", width: 80%),
) <fig-uart-info-1>

Es importante que ambos dispositivos tengan
el mismo baudrate.

Sobre el bit de paridad, solo indica
si se envió bien la información o no.
Si no se mandó, cambia su estado lógico
e indica que hubo un problema.

=== I2C


#figure(
  image("assets/images/i2c-info-1.png", width: 80%),
  caption: [Sobre el protocolo I2C],
) <fig-i2c-info-1>

El esclavo puede responder, pero hay
un poco de incertidumbre.
Se utiliza más para los sensores.

Puedo tener varios esclavos en un mismo puerto de datos
y de reloj.

La cantidad de esclavos es
la cantidad de registros.

*$ 10000 " espacios de registro" arrow "hasta " 10000 " sensores" $*

¿Electrónica digital?

En sí no existe, pero solemos hacerlos discretos
para simplificar el manejo, para abstraerlo.

Para tener cuidados y que no haya problemas,
siempre se tienen que considerar las resistencias.

Para saber qué esclavo recibe info en I2C,
se revisa el Client Address.
Cada vez que envíe datos, tengo que
indicar qué esclavo recibe y opera.

=== SPI

#figure(
  image("assets/images/about-spi-1.png", width: 80%),
  caption: [Sobre el protocolo SPI],
) <fig-about-spi-1>

Utiliza varios buses. El SS es el que
indica el esclavo.
Lo malo es que se necesita un esclavo
por cada pin SS.

Es como una mezcla de UART e I2C, puesto
que tengo un canal de transmisión y
recepción.

=== CAN BUS

#figure(
  image("assets/images/about-can-bus-1.png", width: 80%),
  caption: [Sobre Controller Area Network],
) <fig-about-can-bus-1>

Similar a I2C, solo que la comunicación
es más directa.

= Sobre protocolos de comunicación
== MQTT

#figure(
  image("assets/images/about-mqtt-1.png", width: 80%),
  caption: [Sobre MQTT],
) <fig-about-mqtt-1>

Funciona como un broker; ej, una temperatura
se publica y manda este evento a todos quienes
están suscritos a este evento.
En mi sensor se cargan distintos datos
y quienes están suscritos reciben
estos datos.

== WebSockets

#figure(
  image("assets/images/about-websockets-1.png", width: 80%),
  caption: [Sobre WebSockets],
) <fig-about-websockets-1>

Existe en plataformas como WhatsApp.

El handshake es para confirmar la conexión.

= Comparación de protocolos

#figure(
  image("assets/images/protocols-comp.png", width: 80%),
  caption: [Sobre protocolos de comunicación],
) <fig-protocols-comp>

Sobre robustez, se refiere a qué tan compleja
es su aplicación y qué tan óptimo puede ser.#footnote([
  Esto según el profe; también se puede referir
  a qué tan tolerante a fallos es.
])


Ej: UART es algo compleja, pero si se
siguen sus pasos, no habrá problema.
Hay varios problemas en UART que
van de acuerdo a las definiciones.

= Ejercicio demo python

Código Python:
```python
import serial
import time

PUERTO_SERIAL = "/dev/ttyACM0"
BAUDRATE = 9600

arduino = serial.Serial(PUERTO_SERIAL, BAUDRATE, timeout=1)
time.sleep(2)

while True:
    arduino.write("hola\n".encode())
    print("Python envió: hola")

    respuesta = arduino.readline().decode().strip()
    if respuesta:
        print(f"Arduino respondió: {respuesta}")
        break

    time.sleep(1)

```

Output de la terminal de Linux:

```bash
❯ python3 modulo-2/clase6.py
Python envió: hola
Python envió: hola
Arduino respondió: hola, python
```

Output de la terminal de Arduino IDE V2

```bash
Sketch uses 3508 bytes (1%) of program storage space. Maximum is 253952 bytes.
Global variables use 216 bytes (2%) of dynamic memory, leaving 7976 bytes for local variables. Maximum is 8192 bytes.
```

= Ejercicio 1

`// codigo python`
La idea es que hacer que, dependiendo del color reconocido,
se encienda un LED.

Consideraciones:
- Nos va a mandar una imagen donde tiene el color respectivo,
  dentro de un cuadro.

