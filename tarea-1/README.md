# Tarea 1: Detección y Clasificación de Monedas

Detección y clasificación de monedas venezolanas usando OpenCV (contornos, morfología, circularidad).

## Requisitos

- Python 3.11
- [uv](https://docs.astral.sh/uv/) (opcional, pero recomendado)

## Instalación

### Con uv (recomendado)

```bash
# Crear entorno virtual e instalar dependencias
uv venv --python 3.11
uv pip install -r requirements.txt
```

### Sin uv

```bash
# Crear entorno virtual
python3.11 -m venv .venv

# Activar entorno
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecución

Asegurate de que el entorno virtual esté activado, y luego:

```bash
python "tarea_clase_01_07_detección_y_clasificación_de_monedas.py"
```

> **Nota:** El script usa `matplotlib.pyplot.show()` para mostrar las imágenes, por lo que necesita un entorno gráfico (escritorio). Si estás en un entorno sin GUI (por ejemplo, un servidor), el script fallará al intentar mostrar ventanas. Además, para ir avanzando en la ejecución,
necesita que se presione una tecla (como ALT+F4) para cerrar cada ventana de imagen y continuar con la ejecución del script. El Google Colab
original se encuentra aquí: [https://colab.research.google.com/drive/1588X8XZLJoP9lmQkQrvat3PvfkDPeplM#scrollTo=BRQgibBloEkb](https://colab.research.google.com/drive/1588X8XZLJoP9lmQkQrvat3PvfkDPeplM#scrollTo=BRQgibBloEkb)
