#align(center)[
  = Repaso de la tarea de monedas
  = 06/07/2026
]

= Antecedentes
Se puso a hablar de la tarea y de la transformada de Hough,
ya que esto ayuda a detectar líneas y formas en imágenes, lo cual es útil para identificar monedas en una imagen. La transformada de Hough permite encontrar círculos, que es la forma de las monedas, y así poder contarlas y clasificarlas.

Explica que la finalidad de CV es clasificar cosas.
Nos mostró eso y recapitulamos el código de la
clase 6:


#let python-code = read("../../../modulo-2/clase6.py")

#raw(python-code, lang: "python", block: true)

#pagebreak()
= WebSockets
Se habló sobre cómo se trabaja con WebSockets en
una ESP32.

El código arduino fue el siguiente:

```cpp
#include <WiFi.h>
#include <WebSocketsServer.h>

const char* SSID = "Tu SSID de tu WiFI";
const char* PASSWORD = "Tu contraseña";

WebSocketsServer ws(81);

void onWsEvent(uint8_t client, WStype_t type, uint8_t* payload, size_t len) {
  if (type == WStype_CONNECTED) {
    Serial.println("Cliente conectado!");
  }
  if (type == WStype_DISCONNECTED) {
    Serial.println("Cliente desconectado.");
  }
  if (type == WStype_TEXT) {
    String mensaje = String((char*)payload);
    mensaje.trim();
    Serial.println("Recibido: " + mensaje);

    if (mensaje == "hola") {
      ws.sendTXT(client, "hola python");
    }
  }
}

void setup() {
  Serial.begin(115200);

  WiFi.begin(SSID, PASSWORD);
  Serial.print("Conectando a WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nIP: " + WiFi.localIP().toString());

  ws.begin();
  ws.onEvent(onWsEvent);
  Serial.println("WebSocket server iniciado en puerto 81");
}

void loop() {
  ws.loop();
}```

No puse mi SSID ni mi contraseña porque es privado. xd

El codigo Python fue el siguiente:

```python
import asyncio
import websockets

IP_ESP32 = "192.168.0.21"  # IP que imprime el ESP32 en el Monitor Serial
ESP32_WS_URL = f"ws://{IP_ESP32}:81"



async def saludo():
    while True:
        try:
            async with websockets.connect(ESP32_WS_URL) as ws:
                print("[WebSocket] Conectado a ESP32")
                while True:
                    await ws.send("hola")
                    print("Python envio: hola")

                    respuesta = await ws.recv()
                    print(f"ESP32 respondio: {respuesta}")

                    await asyncio.sleep(1)
        except Exception as e:
            print(f"[WebSocket] Reconectando... ({e})")
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(saludo())
```

= TAREA

Modificar el código de la clase 6 para que funcione con WS.

== Python

#let python-code = read("../../../modulo-2/clase6-b.py")

#raw(python-code, lang: "python", block: true)

== Arduino

```cpp
#include <WiFi.h>
#include <WebSocketsServer.h>

const char* SSID = "MI SSID";
const char* PASSWORD = "MI CONTRA";

WebSocketsServer ws(81);

const int PIN_LED_R = 17;
const int PIN_LED_G = 18;
const int PIN_LED_B = 19;

void apagarTodos() {
  digitalWrite(PIN_LED_R, LOW);
  digitalWrite(PIN_LED_G, LOW);
  digitalWrite(PIN_LED_B, LOW);
}

void onWsEvent(uint8_t client, WStype_t type, uint8_t* payload, size_t len) {
  if (type == WStype_TEXT) {
    String comando = String((char*)payload);
    comando.trim();

    if (comando == "R") {
      apagarTodos();
      digitalWrite(PIN_LED_R, HIGH);
    } else if (comando == "G") {
      apagarTodos();
      digitalWrite(PIN_LED_G, HIGH);
    } else if (comando == "B") {
      apagarTodos();
      digitalWrite(PIN_LED_B, HIGH);
    } else if (comando == "N") {
      apagarTodos();
    }
  }
}

void setup() {
  Serial.begin(9600);

  pinMode(PIN_LED_R, OUTPUT);
  pinMode(PIN_LED_G, OUTPUT);
  pinMode(PIN_LED_B, OUTPUT);
  apagarTodos();

  WiFi.begin(SSID, PASSWORD);
  Serial.print("Conectando a WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nIP: " + WiFi.localIP().toString());

  ws.begin();
  ws.onEvent(onWsEvent);
  Serial.println("WebSocket server en puerto 81");
}

void loop() {
  ws.loop();
}
```

Se probó con un ESP32 y se logró encender los LEDs de colores según el comando enviado desde Python.
