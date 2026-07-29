# Backend FastAPI

API central para controlar el ESP32 maestro y consultar la ESP32-CAM. Esta
primera version no necesita tener el dataset completo
ni embeber el modelo de inferencia en el ESP32-CAM.

## Funciones disponibles

- Consulta de estado del maestro.
- Cambio entre `automatic`, `manual_on` y `manual_off`.
- Prueba directa del rele.
- Consulta de estado y captura BMP de la CAM actual.
- Estado combinado, tolerando que la CAM este apagada por horario.
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
```

## Pruebas

```bash
../../.venv/bin/python -m pytest
```

Las pruebas usan dispositivos simulados; no activan el rele ni requieren que
la ESP32-CAM este encendida.

## Limites de esta etapa

- `/camera/capture` entrega una imagen puntual; el puente de video WebSocket
  se implementara junto con Flutter.
- No hay inferencia, voto mayoritario, base de datos ni notificaciones.
- El token compartido es suficiente para una LAN de desarrollo. La exposicion
  a Internet requerira HTTPS, usuarios y autorizacion individual.
