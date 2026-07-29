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
  LEDs verde y azul, respectivamente, para acelerar
  el proceso de validación de conexión.

  #grid(
    rows: 3,
    row-gutter: 2em,
    align: center,

    apa-figure(
      image(
        "../assets/images/wokwi-before-activation-period.png",
        width: 80%,
      ),
      caption: [Estado del circuito en la simulación previa a la activación],
    ),

    apa-figure(
      image(
        "../assets/images/wokwi-during-activation-period.png",
        width: 80%,
      ),
      caption: [Estado del circuito en la simulación durante el periodo de activación],
    ),

    apa-figure(
      image(
        "../assets/images/wokwi-after-activation-period.png",
        width: 80%,
      ),
      caption: [Estado del circuito en la simulación después del periodo de activación],
    ),
  )

  Según las ilustraciones, se verifica que la sincronización
  del reloj con la hora oficial de Bolivia mediante el protocolo
  NTP se da exitosamente, pudiendo así condicionar
  el encendido o apagado de los componentes simulados.

  Una vez validado el concepto, se procede a implementar el
  hardware real del sistema.

  *Fase 2: Creación del dataset de imágenes.*

  Antes de iniciar la recolección del dataset, se monta el
  ESP32-CAM en una posición fija sobre el alimentador. Durante
  todo el proceso de captura se mantiene el mismo ángulo,
  distancia, orientación y encuadre.

  Debido al espacio disponible en la estructura del alimentador,
  el ángulo de la cámara prioriza la visibilidad del plato. Un
  ángulo orientado directamente hacia la boca del dispensador
  reduciría considerablemente el área visible del plato, que
  constituye la región principal de interés para determinar
  la disponibilidad de alimento.

  Inicialmente se considera separar las imágenes con alimento
  en estados intermedios y llenos. Sin embargo, las pruebas
  preliminares muestran que ambos estados presentan diferencias
  visuales mínimas desde el ángulo disponible. Una vez que el
  alimento cubre la superficie visible del plato, el incremento
  de su cantidad no produce cambios suficientemente distinguibles
  en la imagen.

  #pagebreak()
  Por esta razón, los diferentes niveles con alimento se unifican
  en la clase `food_available`. Se recolectan imágenes para las
  siguientes clases:

  #apa-figure(
    table(
      columns: 2,
      table.header([Clase], [Descripción]),
      [`empty`], [Plato sin alimento visible],
      [`food_available`], [Plato con alimento visible y accesible],
      [`unknown`],
      [
        Escena que no corresponde claramente a las clases anteriores,
        como presencia de la mascota, objetos extraños, suciedad,
        cámara cubierta o una posible obstrucción.
      ],
    ),
    caption: "Clases definidas para el modelo de visión computacional",
    note: "Elaboración propia.",
  )

  La clase `unknown` funciona como una clase de rechazo o
  sumidero. Su propósito es evitar que el modelo asigne
  obligatoriamente una escena anómala a `empty` o
  `food_available`.

  Una clasificación como `unknown` no implica por sí sola
  que exista una obstrucción. Esta condición puede corresponder
  también a la presencia de la mascota, una mano, un objeto
  extraño, suciedad o una oclusión de la cámara.

  La posible obstrucción del mecanismo dispensador se determina
  posteriormente mediante la combinación de las predicciones
  visuales y la lógica temporal del sistema. Por ejemplo, puede
  considerarse una posible obstrucción cuando se activa el
  dispensador y, después del periodo esperado, el plato continúa
  siendo clasificado como `empty` o se obtienen repetidamente
  resultados `unknown`.

  #pagebreak()
  Las capturas se realizan bajo los siguientes contextos
  lumínicos:

  #apa-figure(
    table(
      columns: 2,
      table.header([Periodo del día], [Iluminación]),
      [Mañana], [Luz natural diurna indirecta],
      [Tarde], [Luz natural diurna directa o indirecta fuerte],
      [Noche], [Luz artificial proveniente de la lámpara del ambiente],
    ),
    caption: "Periodos del día durante los cuales se toman las capturas para el dataset",
    note: "Elaboración propia.",
  )


  Al término del proceso de recolección, se cuenta con las
  siguientes cantidades:

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
  16 bits. Por consiguiente, cada captura contiene 153600 bytes
  antes de su conversión o almacenamiento.

  Las capturas son transmitidas desde el ESP32-CAM hasta el
  programa de recolección ejecutado en la computadora. Este
  programa permite visualizar el flujo de imágenes, seleccionar
  la clase correspondiente y almacenar las muestras aceptadas
  dentro de la carpeta asignada a cada clase.

  Como etapa de preprocesamiento, se genera una variante de cada
  captura mediante un filtro mediano con una ventana de 3×3
  píxeles. Este filtro reemplaza el valor de cada píxel por la
  mediana de su vecindad y permite reducir el ruido impulsivo o
  _speckle_ observado en las imágenes RGB565, sin degradar de
  manera significativa los contornos del plato y del alimento.

  La elección de este filtro responde tanto a su capacidad para
  reducir los defectos observados como a la posibilidad de reproducir
  el mismo procesamiento dentro del ESP32-CAM. La mediana de una
  ventana de 3×3 puede implementarse directamente en C o C++ sobre
  los componentes de color de los píxeles RGB565, sin depender de
  OpenCV ni transferir la imagen a otro dispositivo. Además, el
  tamaño reducido de la ventana limita el suavizado de detalles y
  mantiene un costo de memoria y cómputo adecuado para el sistema
  embebido.

  En el despliegue, el flujo se ejecuta íntegramente en el ESP32-CAM:
  el dispositivo captura la imagen RGB565, aplica el filtro mediano,
  la redimensiona a la resolución de entrada del modelo y ejecuta el
  clasificador. De esta forma, el preprocesamiento utilizado al crear
  el dataset también se aplica inmediatamente antes de la clasificación,
  manteniendo consistencia entre el entrenamiento y la inferencia. La
  imagen original y la variante procesada corresponden a una misma
  captura, por lo que no se contabilizan como observaciones
  independientes al describir la cantidad de muestras del dataset.

  *Fase 3: Definición de estrategia de aprendizaje automático y entrenamiento del modelo.*

  #lorem(40)

  *Fase 4: Exportación e importación del modelo en ESP32-CAM.*

  #lorem(40)

  *Fase 5: Desarrollo de los componentes de software.*

  #lorem(40)

  *Fase 6: Despliegue del sistema de monitoreo.*

  #lorem(40)
]
