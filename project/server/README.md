# Backend FastAPI

API central para controlar el ESP32 maestro, consultar la ESP32-CAM y
retransmitir su stream de diagnostico.

## Funciones disponibles

- Consulta de estado del maestro.
- Cambio entre `automatic`, `manual_on` y `manual_off`.
- Prueba directa del rele.
- Consulta de estado, captura BMP e inferencia de la CAM.
- Operacion atomica de captura seguida de inferencia sobre ese frame.
- Puente WebSocket RGB565 con resultados de clasificacion periodicos.
- Estado combinado, tolerando que la CAM este apagada por horario.
- Registro persistente de dispositivos Android y tokens FCM renovables.
- Inicializacion opcional de Firebase Admin mediante una cuenta de servicio.
- Documentacion OpenAPI automatica en `/docs`.

## Instalacion

Desde esta carpeta:

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Las variables de `.env` deben exportarse antes de iniciar el proceso. Uvicorn
no carga ese archivo automaticamente con la configuracion actual:

```bash
set -a
source .env
set +a
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

En desarrollo tambien se puede usar el entorno virtual del repositorio:

```bash
../../.venv/bin/pip install -r requirements.txt
../../.venv/bin/uvicorn app.main:app --reload
```

## Ejemplos

```bash
curl http://SERVIDOR:8000/health

curl -H "X-API-Key: TOKEN_BACKEND" \
  http://SERVIDOR:8000/api/v1/system/status

curl -X POST \
  -H "X-API-Key: TOKEN_BACKEND" \
  -H "Content-Type: application/json" \
  -d '{"mode":"manual_on"}' \
  http://SERVIDOR:8000/api/v1/master/mode

curl -X POST \
  -H "X-API-Key: TOKEN_BACKEND" \
  http://SERVIDOR:8000/api/v1/camera/capture-classify

curl -X POST \
  -H "X-API-Key: TOKEN_BACKEND" \
  -H "Content-Type: application/json" \
  -d '{"installation_id":"instalacion-123","fcm_token":"TOKEN_FCM","platform":"android"}' \
  http://SERVIDOR:8000/api/v1/notifications/devices

curl -H "X-API-Key: TOKEN_BACKEND" \
  http://SERVIDOR:8000/api/v1/notifications/status
```

## Firebase y persistencia

La cuenta de servicio de Firebase debe permanecer fuera del repositorio. En
Docker Compose se monta como archivo de solo lectura y SQLite se conserva en el
volumen `notification-data`.

Variables requeridas en `.env` para el despliegue:

```dotenv
FIREBASE_CREDENTIALS_HOST_PATH=/opt/pet-feeder/secrets/firebase.json
```

Compose configura internamente:

- `FIREBASE_CREDENTIALS_PATH=/run/secrets/firebase.json`
- `NOTIFICATION_DB_PATH=/data/notifications.sqlite3`

Sin `FIREBASE_CREDENTIALS_PATH`, el backend puede iniciar y registrar tokens,
pero no queda habilitado para enviar mensajes mediante Firebase Admin.

## Stream de diagnostico

`WS /api/v1/camera/debug-stream` requiere `X-API-Key` durante el handshake y
solo acepta la conexion si el maestro esta en `manual_on` con el rele activo.
FastAPI abre el WebSocket RGB565 de la CAM, envia `START` y retransmite:

- Mensajes binarios: frames RGB565 de `320x240`.
- Mensaje de texto `stream_config`: formato, dimensiones e intervalo.
- Mensajes de texto `camera_status`: estado del WebSocket de la CAM.
- Mensajes de texto `classification`: resultado de una captura e inferencia.

Ejemplo de mensaje de clasificacion:

```json
{
  "type": "classification",
  "data": {
    "status": "classified",
    "predicted_class": "food_available",
    "confidence": 0.98,
    "frame_id": 12
  }
}
```

Cada ciclo de diagnostico ejecuta primero `/capture` y despues `/classify`.
Esto garantiza que `frame_id` identifica la imagen clasificada. El intervalo se
configura con `DEBUG_CLASSIFICATION_INTERVAL_SECONDS` y es de cinco segundos
por defecto. El stream puede detenerse brevemente mientras la CAM captura e
infiere, porque ambos servicios comparten la misma placa.

El stream de diagnostico no se habilita en `automatic`: las rondas automaticas
se implementaran de forma separada para no mezclar muestras de produccion con
una sesion interactiva.

## Pruebas

```bash
../../.venv/bin/python -m pytest
```

Las pruebas usan dispositivos simulados; no activan el rele ni requieren que
la ESP32-CAM este encendida.

## Limites de esta etapa

- Los dispositivos FCM ya se registran, pero aun no se envian notificaciones.
- SQLite solo contiene dispositivos; faltan rondas, resultados y envios.
- El coordinador de las cinco inferencias automaticas todavia no esta
  implementado.
- El puente retransmite RGB565 sin convertirlo a un formato de video; Flutter
  debera decodificar cada frame o el backend debera incorporar conversion.
- El token compartido es suficiente para una LAN de desarrollo. La exposicion
  a Internet requerira HTTPS, usuarios y autorizacion individual.
