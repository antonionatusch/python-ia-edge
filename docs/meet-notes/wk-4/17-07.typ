#import "@preview/cmarker:0.1.2": render

#set text(lang: "es")
#align(center)[
  = Clase 12: Optimización de modelos de ML
  = 17/07/2026
]
#set heading(numbering: "1.")
= Previo a la clase
Las clases terminan el siguiente viernes.


= Sobre optimizaciones y Edge AI
Suele ser un proceso cíclico.

Sus objetivos son:

- Reducir memoria RAM
- Reducir memoria Flash
- Disminuir el tiempo de inferencia
- Reducir el consumo energético
- Mantener una alta precisión

En el peor de los casos, al menos
uno de estos objetivos se cumple.

No se suele usar Arduino ya que suele
ser lento.

= Estrategias de optimización

- Cuantización
- Pruning
- Knowledge Distillation
- Compresión de modelos
- Arquitecturas ligeras (MobileNet, EfficientNet)

El flujo típico es:

*$ "Modelo entrenado" arrow "Optimización"
arrow "Modelo ligero" arrow "Procesamiento" arrow "Despliegue en EDGE AI" $*

Entra en mayor detalle de cada una de estas estrategias en
la presentación; se puede ver en @md-resources.

= Algunas notas de algunas técnicas
- En el pruning, suele ser necesario hacer Fine-Tuning para recuperar la precisión.
  Esto significa sacar nuevas fotos y volver a entrenar el modelo.

= Recomendaciones para trabajar con ESP32

- TFLite Micro
- Modelos cuantizados
- INT8
- Imágenes pequeñas (96x96 o menores)
- Reducir número de capas
- Reducir número de parámetros

= Aplicaciones
- Reconocimiento de gestos
- Clasificación de sonidos
- Detección de movimiento
- Sensores inteligentes

= Flujo completo de optimización

#figure(
  image("assets/images/opt-complete-flow.png", width: 80%),
  caption: [Sobre optimización de modelos de CV para EDGE AI],
) <fig-opt-complete-flow>

= Práctica
Vamos a entrenar un modelo, intentar desplegarlo,
y mostrar la salida.

= Notas post clase
Podemos usar plataformas no code / Transfer Learning.

Se sacan las clases y uno saca las clases con ese modelo.

Se puede tener un buen resultado/desempeño.

Lo vamos a ver en una futura clase.

= Código Python - Árbol de decisión interactivo con Arduino

#let python-code-class = read("../../../modulo-3/clase-12Teacher.py")

#raw(python-code-class, lang: "python", block: true)

`todo: agregar otros scripts de Python y de Arduino`

Observación: El tamaño de imagen que le pasa
a la placa importa mucho.

Si la diferencia a través de las épocas
de pérdida es menos de 0.0005,
tocaría probar las capas ocultas
o cosas así.

Dudas:
- ¿Cosa con mayor incidencia en la precisión (dataset, capas)?
  - En el caso de dataset chico, como el profesor
    detectaba bien, no es culpa de eso. Podríamos
    aumentar la cantidad de imágenes para que tenga
    preferencia con el entorno.
    El learning rate (TASA_APRENDIZAJE) igual
    se puede subir para que tenga más de confianza
    el estudiante. Lo malo de esto es que
    le instamos a que sea más preciso, lo que hace
    que el modelo sea más pesado.
    Mantener menos de 85% de uso de memoria RAM
    en lo posible.

    Lo que el profe haría es que subiría el
    alfa distillation, neuronas ocultas y
    tamaño del estudiante.
- ¿Escala estudiante hasta donde dé la cam de streaming continuo?
  - La idea es que con la misma imagen
    tengan la misma detección.
    No recomienda trabajar con
    los frames; en lo general, se tiene que estar
    por debajo de 100 pixeles.

    Se puede usar el teorema de Nyquist,
    gradiente de imagen, entropía, etc.
    para saber cuál es el tamaño óptimo.
    Se puede trabajar con 120x120,
    de repente.



#figure(
  image("assets/images/demo-prof.png", width: 80%),
) <fig-demo-prof>

No detecta mucho; signo de overfitting
posible.

#{
  set text(size: 31pt)
  align(center)[MIÉRCOLES 22 07 REVISA AVANCE, presentar arquitectura,
    diseño.]
}

= Recursos Markdown <md-resources>
#render(read("../../RESOURCES.md"))
