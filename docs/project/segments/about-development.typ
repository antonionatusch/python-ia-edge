#import "../utils/figures.typ": apa-figure
#let about_development = [
  De forma estructural, se puede desglosar
  el desarrollo del proyecto en las siguientes fases:

  *Fase 0: Adquisición de materiales.*

  Previo a realizar cualquier esfuerzo de diseño e implementación,
  se adquieren los siguientes materiales considerando
  las necesidades de hardware del sistema:

  #apa-figure(
    table(
      columns: 5,
      table.header([Componente], [Cantidad utilizada], [Especificación], [Uso en el sistema], [Precio de compra]),
      [], [], [], [], [],
      [], [], [], [], [],
      [], [], [], [], [],
      [], [], [], [], [],
      [], [], [], [], [],
    ),
    caption: "Tabla de materiales adquiridos para el hardware del sistema de monitoreo",
    note: "Elaboración propia.",
  )

  *Fase 1: Diseño e implementación de componentes de hardware.*

  Antes de armar en físico el circuito de hardware del sistema,
  es prudente diseñar, imitando lo mejor posible el funcionamiento
  esperado, el sistema antes de pasar a la implementación real
  de los componentes involucrados.
  Tomando en cuenta su facilidad de uso, se opta por usar
  Wokwi. Wokwi es una herramienta un simulador de
  componentes electrónicos online que se puede usar
  para simular placas como Arduino, ESP32, STM32
  y muchas otras placas, partes y sensores populares. @WokwiWelcome2026

  Para sustituir el ESP32-CAM y el ventilador, se utilizan
  LEDs verde y azul (respectivamente) para acelerar
  el proceso de validación de conexión.

  #grid(
    rows: 3,
    row-gutter: 2em,
    align: center,

    apa-figure(
      image("../assets/images/wokwi-before-activation-period.png", width: 80%),
      caption: [Estado del circuito en la simulación previa activación],
    ),

    apa-figure(
      image("../assets/images/wokwi-during-activation-period.png", width: 80%),
      caption: [Estado del circuito en la simulación durante el periodo de activación],
    ),

    apa-figure(
      image("../assets/images/wokwi-after-activation-period.png", width: 80%),
      caption: [Estado del circuito en la simulación después del periodo de activación],
    ),
  )

  Según las ilustraciones, se verifica que la sincronización
  del reloj
  con la hora oficial de Bolivia mediante el protocolo
  NTP se da exitosamente, pudiendo así condicionar
  el encendido o apagado de los componentes simulados.

  Una vez validado el concepto, se procede a implementar el
  hardware real del sistema.

  *Fase 2: Creación del dataset de imágenes.*

  Se recolectan imágenes para las clases:

  #apa-figure(
    table(
      columns: 2,
      table.header([Clase], [Descripción]),
      [`empty`], [Plato sin alimento visible],
      [`food_available`], [Plato con alimento visible y accesible],
      [`unknown`],
      [Escena que no corresponde claramente a las clases anteriores, como presencia de la mascota, objetos extraños, suciedad, cámara cubierta o una posible obstrucción],
    ),
    caption: "Clases definidas para el modelo de visión computacional",
    note: "Elaboración propia.",
  )

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

  #pagebreak()
  Al término del proceso de recolección, se cuenta con las siguientes cantidades:

  #apa-figure(
    table(
      columns: 5,
      table.header([Clase], [Mañana], [Tarde], [Noche], [Total por clase]),
      [`empty`], [a], [a], [a], [t],
      [`food_available`], [a], [a], [a], [t],
      [`unknown`], [a], [a], [a], [t],
      [Total por periodo], [$sum_i^n a$], [$sum_i^n a$], [$sum_i^n a$], [$sum_i^n t$],
    ),
    caption: "Distribución de las muestras del dataset final",
    note: "Elaboración propia.",
  )

  Cada imagen es capturada originalmente con una resolución
  de 320×240 píxeles en formato RGB565. Debido a que el sensor
  GC2145 incorporado en el módulo utilizado no proporciona
  compresión JPEG por hardware, cada píxel se representa mediante
  16 bits, por lo que cada captura ocupa 153600 bytes antes de su
  conversión o almacenamiento.

  *Fase 3: Definición de estrategia de aprendizaje automático y entrenamiento del modelo.*

  #lorem(40)

  *Fase 4: Exportación e importación del modelo en ESP32-CAM.*

  #lorem(40)

  *Fase 5: Desarrollo de los componentes de software.*

  #lorem(40)

  *Fase 6: Despliegue del sistema de monitoreo.*

  #lorem(40)
]
