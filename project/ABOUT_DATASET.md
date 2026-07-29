# Dataset de imágenes — Monitoreo de plato de alimentador

## Objetivo del dataset

Entrenar un modelo de clasificación de imágenes con Edge Impulse
(MobileNetV1, entrada 96×96, cuantización INT8) que detecte
el estado del plato de un alimentador para mascotas.

## Clases

| Clase | Descripción |
|---|---|
| `empty` | Plato completamente vacío |
| `food_available` | Plato con alimento visible y accesible |
| `unknown` | Escena que no corresponde claramente a las clases anteriores |

## Períodos del día

Cada clase se captura en tres condiciones de iluminación distintas:

- **Mañana:** luz natural diurna indirecta
- **Tarde:** luz natural diurna directa o indirecta fuerte
- **Noche:** luz artificial (lámpara del ambiente)

La iluminación es el factor de variación más importante para la
generalización del modelo. No se debe mover la cámara entre sesiones
del mismo período.

## Cantidades mínimas recomendadas

| Clase | Mañana | Tarde | Noche | Total por clase |
|---|---|---|---|---|
| `empty` | 25 | 25 | 25 | **75** |
| `food_available` | 25 | 25 | 25 | **75** |
| `unknown` | 25 | 25 | 25 | **75** |
| **Total por turno** | 75 | 75 | 75 | **225** |

### Por qué 25 por sesión

- **Mínimo absoluto (15 por sesión / 180 total):** funciona, pero el
  modelo puede overfittear a pocas condiciones de iluminación.
- **Recomendado (25 por sesión / 300 total):** buen balance entre
  esfuerzo de captura y generalización.
- **Ideal (40–50 por sesión / 480–600 total):** más robusto, pero
  requiere más tiempo y cuidado en la recolección.

## Procedimiento de captura

1. **Fijar la cámara** en su posición final apuntando al plato.
   No moverla durante todo el proceso de captura.
2. **Capturar 25 fotos por clase** en un turno completo (mañana,
   tarde o noche). Dentro de cada sesión, variar sutilmente:
   - La cantidad y distribución del alimento
   - La posición exacta del plato (si es posible)
   - Ángulos mínimos de la cámara (solo si no se altera la posición fija)
3. **No variar la iluminación** dentro de una misma sesión.
   La iluminación se controla cambiando entre turnos.
4. **Repetir** el paso 2 para cada turno del día.
5. **Validar visualmente** una muestra de cada sesión antes de
   continuar con la siguiente.

## Errores comunes a evitar

- Tomar todas las fotos en un solo turno (sin diversidad de iluminación)
- Mover la cámara entre clases (rompe la consistencia espacial)
- Capturar muy rápido sin variar la escena (fotos casi idénticas)
- Mezclar zooms o filtros entre clases sin registro en metadata

## Estado actual del dataset

| Clase | Mañana | Tarde | Noche | Total |
|---|---|---|---|---|
| `empty` | 25 | 25 | 14 | 64 |
| `food_available` | 28 | 25 | 18 | 71 |
| `unknown` | 25 | 0 | 40 | 65 |

**Total:** 200 fotos

## Plan de captura

### Pendiente
- `empty`: 11 fotos en la noche
- `food_available`: 7 fotos en la noche
- `unknown`: 25 fotos en la tarde

### Meta final
- 75 fotos por clase
- 225 fotos totales
- 3 condiciones de iluminación por clase
