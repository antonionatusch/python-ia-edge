#import "../utils/figures.typ": apa-figure

#let system_pipeline = [
  Antes de hablar del pipeline mismo del sistema,
  es conveniente explicar el desarrollo
  que tuvo lugar previo a explicar el pipeline
  completo.

  == Desarrollo del proyecto según sus distintas fases

  *Fase 0: Adquisición de materiales.*

  Previo a realizar cualquier esfuerzo de diseño e implementación,
  se adquieren los siguientes materiales considerando
  las necesidades de hardware del sistema:

  #apa-figure(
    {
      show table.cell: set text(size: 10pt)
      table(
        columns: 5,
        table.header(
          [Componente], [Cantidad utilizada], [Especificaciones], [Uso en el sistema], [Precio unitario de compra]
        ),
        [ESP32 38Pin WiFi-Bluetooth],
        [1 unidad],
        [Conector tipo C, Conversor USB-Serial 2102, Módulo ESP32-WROOM-32],
        [Unidad central de procesamiento de eventos, control de relé.],
        [Bs. 100],

        [ESP32-CAM GC2145],
        [1 unidad],
        [16 pines, 3.3/5 V, 520 KB SRAM + 4M PRAM],
        [Captura de fotogramas, inferencia sobre imágenes de plato.],
        [Bs. 150],

        [Conector WAGO de 4 vías], [6 unidades], [-], [Conexión entre componentes.], [Bs. 15],

        [Modulo Relay 1CH Canal 5VDC Optoacoplado],
        [1 unidad],
        [1 canal de salida, nivel de disparo en HIGH, relé de tensión de carga: 125VAC/250VAC

          28VDC/30VDC],
        [Activación de ventilador y ESP32-CAM.],
        [Bs. 20],

        [Ventilador DC5V],
        [1 unidad],
        [Fuente de alimentación: DC 5V, 30x30x10 mm],
        [Refrigeración de ESP32-CAM.],
        [Bs. 20],

        [Cable AWG], [1 metro], [-], [Conexión entre los componentes del circuito.], [Bs. 2],

        [Diodo rectificador 1N4007],
        [1 unidad],
        [Voltaje repetitiva inversa de pico: 1000 Volts, Capacitancia total \@ 4V, 1 MHz: 15 pF],
        [Rectificación de corriente, protección contra polaridad inversa.],
        [Bs. 0,50],

        [Capacitor cerámico 100 $n"F"$], [1 unidad], [-], [Desacoplo y filtrado de ruido.], [Bs. 0,50],

        [Capacitor electrolítico 100 $mu"F"$],
        [1 unidad],
        [-],
        [Estabilización de alimentación ante variaciones de carga.],
        [Bs. 1,50],

        [Total], [], [], [], [Bs. $#(100 + 150 + 6 * 15 + 20 + 20 + 2 + 0.50 + 1.50)$],
      )
    },
    caption: "Tabla de materiales adquiridos para el hardware del sistema de monitoreo",
    note: "Elaboración propia. Los precios pueden variar según la electrónica donde se busque la pieza.
    Materiales que están en el circuito pero no listados aquí estaban disponibles previo a la
    realización del proyecto, por lo cual no se toman en cuenta.",
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
      [`empty`], [25], [25], [35], [85],
      [`food_available`], [28], [33], [42], [103],
      [`unknown`], [25], [25], [40], [90],
      [Total por periodo], [78], [83], [117], [278],
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

  Para la estrategia de aprendizaje automático, se opta por
  usar Transfer Learning, la cual
  es una técnica de aprendizaje automático
  (o machine learning) donde
  un modelo que se desarrolla
  para una tarea específica se reutiliza como el
  punto de partida para otra tarea similar.

  Se opta
  por usar esta técnica ya que esto permite acelerar
  el proceso de entrenamiento, ayuda a trabajar mejor
  con datasets pequeños ya que el modelo conoce
  patrones básicos de antemano, y suele ofrecer
  una mejor precisión dependiendo del modelo
  que se use.

  Para entrenar el modelo, se usa Edge Impulse como
  plataforma principal de desarrollo. Esta plataforma está
  orientada a la creación de modelos de aprendizaje automático
  para sistemas embebidos y
  dispositivos con recursos limitados,
  por lo que permite
  organizar en un mismo entorno la carga del
  dataset, el diseño
  del flujo de procesamiento, el entrenamiento,
  la evaluación y la exportación del modelo.

  Dentro del proyecto se
  configura un impulso de clasificación de
  imágenes con una entrada
  de 96×96 píxeles y tres clases:
  `empty`, `food_available` y `unknown`.
  Como bloque de aprendizaje
  se utiliza Transfer Learning con MobileNetV1 96×96 0.25, una
  arquitectura reducida pensada para dispositivos de borde.

  Edge Impulse también permite
  visualizar las características
  extraídas, revisar la
  matriz de confusión y evaluar el modelo
  sobre un conjunto de
  prueba separado. Aunque durante la validación
  se obtiene una precisión
  del 100 %, la prueba con imágenes no
  utilizadas en el entrenamiento
  alcanza una precisión general
  del 86,44
  %, mostrando que la
  clase `unknown` es la más difícil
  de reconocer de forma consistente.

  Finalmente, la plataforma
  permite cuantizar el modelo a `int8`
  y estimar sus requerimientos
  de memoria, almacenamiento y tiempo
  de inferencia antes de
  llevarlo al microcontrolador. También se
  utiliza el compilador EON
  y se exporta el proyecto como una
  librería de Arduino,
  incluyendo en un mismo paquete el
  preprocesamiento, los pesos
  de la red neuronal y el código
  necesario para ejecutar la
  clasificación en el dispositivo.

  *Fase 4: Exportación e importación del modelo en ESP32-CAM.*

  Se importa la
  librería descargada de Edge Impulse y se usa el código
  provisto para embeber tanto la lógica de hardware y de
  inferencia como la de negocio,
  esta última estando establecida según
  el fin del proyecto. Para mayor detalle, es
  posible consultar el repositorio
  de código hospedado en GitHub en el Anexo A. `// agregar anexos`

  *Fase 5: Desarrollo de los componentes de software.*

  #lorem(40)

  *Fase 6: Despliegue del sistema de monitoreo.*

  #lorem(40)
]
