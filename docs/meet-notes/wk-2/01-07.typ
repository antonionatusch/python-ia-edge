#let jupyter-in(code, num: "") = block(
  fill: rgb("f7f7f7"),
  inset: 8pt,
  radius: 4pt,
  width: 100%,
  stroke: 0.5pt + rgb("e0e0e0"),
  grid(
    columns: (40pt, 1fr),
    text(font: "Liberation Mono", size: 8pt, fill: rgb("303f9f"))[In [#num]:], raw(code, lang: "python"),
  ),
)

#let jupyter-out(content, num: "") = block(
  inset: (left: 8pt, right: 8pt, bottom: 8pt),
  width: 100%,
  grid(
    columns: (40pt, 1fr),
    text(font: "Liberation Mono", size: 8pt, fill: rgb("d84315"))[Out[#num]:], content,
  ),
)

#align(center)[
  = Clase 4
  = Clasificaciones mediante operaciones morfológicas
  = 07/01/2026
]

= Antes de la clase
Vimos un poquito lo que hizo el profe.

Sobre CLAHE

#jupyter-in(
  "clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))\nresultado = clahe.apply(imagen)\ncv2_imshow(resultado)",
  num: "1",
)

El parámetro `clipLimit` es el límite de contraste
para la ecualización del histograma. Un valor más alto
significa que se permite un mayor contraste en la imagen
resultante, mientras que un valor más bajo limita el
contraste.

En la versión que va explicando el profe, el
destello que había antes podía hacer que el contorno sea
más difuso.

Luego, le aplica un filtro espacial Gaussiano de 7x7.

#jupyter-in("blur = cv2.GaussianBlur(resultado, (7, 7), 0)", num: "2")

Luego, había un problema con el filtro binario.

#jupyter-in(
  "_, binary = cv2.threshold(\n    blur,\n    0,\n    255,\n    cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU\n)\ncv2_imshow(binary)",
  num: "3",
)

El problema de esto es que hacía que se consideren contornos.

Si estuviera junto, habría un problema diferente; se
interpretaría como un contorno grande, y no se podría
separar.

= Sobre colores vs contornos
Se puede identificar por color, y clasificar. En la práctica,
la moneda de Bs. 5 se pueden identificar por color y el resto por área.

En el trabajo, depende de la creatividad del ingeniero. Lo que importan,
sobre todo, son los resultados.

= Sobre segmentación de imágenes

Es dividir una imagen en regiones homogéneas o
significativas.

*$ "El objetivo es separar objetos de interés del fondo." $*

Ecuación formal:

$ I(m,n) arrow {R 1, R 2, dots, R k} $

Donde:
- $I(m,n)$ es la imagen de entrada, y
- ${R 1, R 2, dots, R k}$ son las regiones segmentadas de la imagen.

== Basada en umbralización
=== Global
Selecciona un único umbral T.


Se podría binarizar con el threshold de Trunc o usar la máscara,
lo cual ayuda a segmentar, de cierta forma, las monedas en el caso
de las monedas que están juntas.

Para ver qué método implementar, se recomienda, en este caso,
aplicar todas las herramientas y ver cuál se va acomodando mejor
al objetivo.

Es un poquito tosca; dependiendo del ruido, puede
sacar una buena imagen
de RGB pero en otras escalas no.

=== Adaptativa

Toma regiones y considera la umbralización de un
threshold calculado en esa región.

Se suelen usar:
- Umbral de media
- Gaussiana

Dependen de un kernel, pero OpenCV ya lo tiene definido.
Uno solo define la región.

=== Método de Otsu

Calcula automáticamente el umbral óptimo
minimizando la varianza intra-clase.

Método matemático que ve si es conveniente
llevarlo a negro o blanco; trata de analizar todo
el contexto y ve si vale la pena llevarlo a uno u otro.

Ventajas:
- Automático, no se necesita definir parámetros.
- Funciona como texto sobre una hoja.
  - En el caso de las monedas, Otsu no funciona mucho por los destellos.

Limitaciones:
- Si no es un histograma bimodal, no funciona tan bien.

== Basada en color
=== RGB
Se definen rangos en cada canal.

Ventajas:
- Suele ser compatible de forma nativa con la mayoría de las cámaras.

Limitaciones:
- Mezcla la info del color con la del brillo, alta sensibilidad.
  Se recomienda convertir la imagen a HSV.


=== LAB
L = luminosidad
a = información de color de un canal
b = información de color de otro canal???

== Basada en regiones
=== Region growing
Agrupa pixeles vecinos con características similares

=== Connected components
Agrupa pixeles conectados en regiones independientes.

=== Split and merge
Organiza una imagen usando una estructura de
datos de árbol cuaternario.

== Basada en bordes
Similar a lo anterior, pero en base al área.

= Objetivos de segmentación
Deberíamos poder hacer:

== Segmentación semántica
Intenta ver todo el contexto de la imagen.

== Segmentación de instancias
Identifica no solo las regiones
sino también los objetos de interés.

== Segmentación panóptica
Analiza las regiones, las clasifica,
y a los objetos los puede clasificar según
su cardinalidad, por ejemplo.

== Notas sobre conocimiento de dominio
Uno no suele elegir al 100%; uno suele
hacer uso de las herramientas conocidas
para hacer el mejor esfuerzo.

Sobre el overfitting, va más al
lado de machine learning y deep
learning.

En VC, la idea es que haga overfitting,
ya que analizamos un caso en concreto.

Queremos analizar cómo clasificar
monedas en específico.

Para generalizar, se usan
otros algoritmos. Cuando vemos la parte de IA,
se torna pesado.

Lo que nos mostró hasta ahora,
digamos que no sirve de nada porque con una
llamada a una API ya fue.

Como "tarea" aparte, hasta que no nos ensuciemos
las manos, quizás no entendamos bien cómo
funca la visión computacional.

Primero tenemos que ver cómo funciona por detrás
hasta llegar el microcontrolador, después podemos ver
cosas relacionadas a IA.

Probablemente no vamos a recibir buenos resultados
si no hacemos preprocesamiento adecuado (operaciones
morfológicas).

= Mini tarea
Importar las clases y ver cuál utilizar y
cuál no.

En cada operación del main, se aplica a una misma imagen.

Lo único que hacemos es ver el resultado.

Hay que ver cómo optimizar; cambiar nombres
de variables, nombres de funciones y hacer
una función main que cumpla algo.

Ej: Se puede hacer lo de las monedas
tanto en Colab como en el editor.

Una vez tenemos algo confiable, lo hacemos en Python
y tratamos de aplicar las mismas operaciones.

= Tarea adelantada
Preguntar a GPT o investigar:
Si identificar color rojo,
el led se encienda rojo.
Si hay algún objeto azul, que se encienda de azul.
Si hay algo de color verde, que lo encienda de verde.

Cuando trabajamos en programación,
solemos cambiar el código de alguien más.

Sobre la tarea adelantada:
- ¿Necesitamos usar un fondo suave?
  - No, hacer un modelito más pendejo.

- ¿Grabar?
  - No, tenemos que mostrarlo en clase.

- ¿Correr OpenCV en ESP?
  - Enviamos datos de forma serial.
    - Primero CV, luego un canal de información,
      y, una vez enviado por ese canal,
      el $mu C$ hace algo.


== Tarea inmediata
Implementar soluciones ya vistas antes
y con la segmentación para lo de las monedas.

No necesitamos llegar a un resultado top,
pero al menos tenemos que ver cómo llegar a clasificar
esto.

Organizar nuestras propias funciones dentro de VSCode.
