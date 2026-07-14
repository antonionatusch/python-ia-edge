#align(center)[
  = Módulo 3 - Clase 10
  = 13/07/2026
]

= Previo al contenido
Preguntó si habíamos hecho la tarea
(no lo hice xd).

Dijo que se puede usar la IA, pero si la usamos,
que no haga todo de forma perfecta.
No hacer más allá del prompt inicial.

Va a mandar _papers_ para leer
el cual el profe considera que son
necesarios.

Se pueden definir los proyectos ya que hay que
empezar a trabajar.

= Sobre MediaPipe#footnote()[#link("https://developers.google.com/edge/mediapipe/solutions/guide")]
Es una librería de Python provisto por Google
que ayuda
a detectar distintas cantidades de objetos.
Puede poseer animales, partes del cuerpo,
etc.

MediaPipe usa grafos.
La ventaja de trabajar con grafos
frente a otras cosas es que cada nodo
del grafo realiza una tarea específica.
Es como una red neuronal con pequeñas
secciones que poseen especificaciones.

Además, varios de sus modelos están
optimizados para computación
embebida.

Otra ventaja de MediaPipe es que
tiene procesamiento RAG.

== Sobre landmarks
Son puntos específicos en, al menos según el ejemplo,
una articulación.

#figure(
  image("./assets/img/mediapipe-landmarks.png", width: 60%),
  caption: [Landmarks de la mano],
)

== Sobre preprocesamiento
Los algoritmos están bastante bien optimizados,
así que no es necesario. Se le manda una imagen
en bruto y así nomás funca.

= Pequeña tarea para 15/07
Usar el código para que, dependiendo de la cantidad
de dedos, se enciendan los leds.

Particularmente:
- Conectar 3 LEDs al arduino de cada color.
- Hay que mostrar el color en particular, junto con la cantidad de dedos.
- Si usamos el ejemplo del profe, se usa rojo, verde y azul.
- Si mostramos el color rojo y levantamos <= 3 dedos, se encienden 1, 2, 3 LEDs.
- $> 5 "LEDs"$, se encienden todos.
- $0 "dedos"$, no se enciende ninguno.
- La comunicación puede ser WebSockets o serial.
- Indica que sirve para entender cómo se va armando y estructurando el ciclo.

= Sobre Inteligencia Artificial

#figure(
  image("assets/images/ai-by-capacity.png", width: 80%),
  caption: [IA según capacidad],
) <fig-ai-by-capacity>

Actualmente, recién estamos entrando a la IA general,
con ejemplos como Claude, ChatGPT, etc.


#figure(
  image("assets/images/ay-by-functionality.png", width: 80%),
  caption: [IA según su funcionalidad],
) <fig-ay-by-functionality>

Sobre mecánica reactiva, lo malo es que necesitaba
muchos recursos computacionales.

Sobre memoria limitada, ya quiere funcionar
como una charla con un humano, pero sigue
dependiendo del servidor.

Sobre teoría de la mente, la idea
es que no responda solo lo que necesite
sino que también tenga sentimientos o
emociones (o, al menos, sepa procesarlos).

Sobre self-awareness, es como lo de las pelis. xd


#figure(
  image("assets/images/ai-acc-theory.png", width: 80%),
  caption: [Sobre la IA según la teoría],
) <fig-ai-acc-theory>


#figure(
  image("assets/images/ml-classif.png", width: 80%),
  caption: [Sobre tipos de ML],
) <fig-ml-classif>

Sobre el self-supervised,
se están dando los autoencoders,
los cuales sirven para restaurar imágenes.
También hay algoritmos que ayudan
con edge computing.

= Código Python en clase

#let python-code-class = read("../../../modulo-3/clase-10.py")

#raw(python-code-class, lang: "python", block: true)


= Código Python tarea
`// TODO`
= Código Arduino tarea
`// TODO`
