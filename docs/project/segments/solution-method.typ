#import "../utils/figures.typ": apa-figure
#let solution_method = [
  El método de solución para el presente trabajo consiste
  en desarrollar el sistema de monitoreo, el cual incluye
  componentes de hardware tipo SoC (_system on
  a chip_, por sus siglas en inglés @DigiInternationalSoCDefinition), procesamiento
  y envío de imágenes mediante protocolos de comunicación
  remotos, manejo y emisión
  de eventos según la clasificación
  del modelo de visión computacional y presentación
  de la información procesada a un cliente móvil
  usando una aplicación creada en Flutter.

  La validación se da mediante
  la comparación entre las clasificaciones
  del modelo y la imagen real del plato,
  revisión de bitácoras (o _logs_, según
  su palabra en inglés) para corroborar
  la verosimilitud de los eventos
  anunciados en el sistema y la retroalimentación
  provista por los instructores del curso
  en la presentación del proyecto.

  De forma estructural, se puede desglosar
  el desarrollo del proyecto en las siguientes fases:

  *Fase 0: Adquisición de materiales.*

  #lorem(40)

  *Fase 1: Diseño e implementación de componentes de hardware.*

  #lorem(40)

  *Fase 2: Creación del dataset de imágenes.*

  Se recolectan imágenes para las clases:

  #apa-figure(
    table(
      columns: 2,
      table.header([Clase], [Descripción]),
      [`empty`], [Plato completamente vacío],
      [`half_full`], [Plato con alimento a nivel medio],
      [`full`], [Plato con alimento al máximo],
      [`obstructed`], [Plato obstruido (objeto, suciedad, mascota)],
    ),
    caption: "Clases para el modelo de visión computacional",
    note: "Elaboración propia.",
  )

  #pagebreak()
  Bajo los siguientes contextos lumínicos:

  #apa-figure(
    table(
      columns: 2,
      table.header([Periodo del día], [Iluminación]),
      [Mañana], [luz natural diurna indirecta],
      [Tarde], [luz natural diurna directa o indirecta fuerte],
      [Noche], [luz artificial (lámpara del ambiente)],
    ),
    caption: "Periodos del día durante los cuales se toman las capturas para el dataset",
    note: "Elaboración propia.",
  )

  Al término del proceso de recolección, se cuenta con las siguientes cantidades:

  #apa-figure(
    table(
      columns: 5,
      table.header([Clase], [Mañana], [Tarde], [Noche], [Total por clase]),
      [`empty`], [a], [a], [a], [t],
      [`half_full`], [a], [a], [a], [t],
      [`full`], [a], [a], [a], [t],
      [`obstructed`], [a], [a], [a], [t],
      [Total por turno], [$sum_i^n a$], [$sum_i^n a$], [$sum_i^n a$], [$sum_i^n t$],
    ),
    caption: "Muestras tomadas para el dataset final",
    note: "Elaboración propia.",
  )

  Cada imagen capturada es almacenada en su resolución original de
  160×120 píxeles (formato RGB565, conversión a BMP mediante
  `frame2bmp()` de la librería `esp32-camera`). Adicionalmente,
  se genera una versión procesada sometida a un filtro de realce
  de luminancia mediante _Contrast Limited Adaptive Histogram
  Equalization_ (CLAHE), con los siguientes parámetros: un límite
  de recorte (`clipLimit`) de 1,5 y una cuadrícula de ecualización
  de 8×8 bloques. Este filtro se aplica únicamente al canal de
  luminancia en el espacio de color LAB, preservando intactos
  los canales de crominancia (A y B), lo que mejora el contraste
  local sin alterar la información cromática de la imagen.

  #pagebreak()

  *Fase 3: Definición de estrategia de aprendizaje automático y entrenamiento del modelo.*

  #lorem(40)

  *Fase 4: Exportación e importación del modelo en ESP32-CAM.*

  #lorem(40)

  *Fase 5: Desarrollo de los componentes de software.*

  #lorem(40)

  *Fase 6: Despliegue del sistema de monitoreo.*

  #lorem(40)
]
