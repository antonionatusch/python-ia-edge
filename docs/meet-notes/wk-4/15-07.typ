#set text(lang: "es")
#align(center)[
  = Clase 11: Sobre Edge Computing
  = 15/07/2026
]

= Previo a la clase
Preguntó sobre las tareas de ML.

También preguntó sobre la tarea de los leds
(ver: apuntes del 13 de junio)

= Código Tarea LEDs
Sobre el buffer de los FPS,
es necesario porque así sabemos
cuál es la potencia del procesador.

Es bastante similar a lo que hicimos
en las anteriores 2 tareas.

`//TODO: pedir el código xd`

= Sobre el proyecto
Es mejor usar el servidor de mi laptop.
La idea es que todo se procese dentro del microcontrolador, ya que eso
es Edge Computing en sí.

= Edge Computing

#figure(
  image("assets/images/about-edge-computing-1.png", width: 80%),
  caption: [Sobre Edge Computing],
) <fig-about-edge-computing-1>

En cloud computing, toda la data está en la nube;
la diferencia de esto con Edge Computing es
priorizar el procesamiento de la información
en el microcontrolador.

- Flujo tradicional: Sensor #sym.arrow Internet
  #sym.arrow Cloud #sym.arrow Procesamiento #sym.arrow Respuesta
- Flujo tradicional: Sensor #sym.arrow Dispositivo Edge
  #sym.arrow Procesamiento Local #sym.arrow Respuesta inmediata


== Sobre ventajas y desventajas

#figure(
  image("assets/images/edge-adv-disadv.png", width: 80%),
  caption: [Sobre ventajas y desventajas de Edge Computing],
) <fig-edge-adv-disadv>


== Sobre restricciones
Las restricciones que posee están relacionadas
a una potencia no muy grande junto a la necesidad
de estar alimentado por batería.

Por ello, es necesario diseñar modelos
pequeños, rápidos y eficientes.

Para ver otras imágenes, se puede inspeccionar
`RESOURCES.md` para hacer clic al Canva.

== Sobre pipeline de TinyML (tipo de ML a usar en el proyecto)

#figure(
  image("assets/images/about-tinyml-pipeline.png", width: 80%),
  caption: [Sobre pasos de TinyML],
) <fig-about-tinyml-pipeline>

Resaltan los pasos 2-4 y 6.

En el caso de mi proyecto, tengo que sacar
un montonazo de fotos (quizás) de los
platos de comida.

Lo malo de usar eso es que vamos a tener
fotos pesadas.

Hasta cierto punto, toca procesar imagen
por imagen.

== Sobre selecciones de hardware


#figure(
  image("assets/images/hardware-choice-projects.png", width: 80%),
  caption: [Sobre opciones de hardware según proyecto],
) <fig-hardware-choice-projects>

= Observaciones fuera del tema
La programación agéntica es interesante;
sin embargo, para el contexto de este proyecto,
no va a solucionar absolutamente todo.
La idea es que nosotros, conociendo el tema,
sepamos discernir la calidad del código.

= Sobre el proyecto y su entorno
La idea es que trabajemos en un
entorno controlado.
El sistema podría tener un foco LED
o algo parecido el cual ayude al sistema
a que pueda detectar lo preciso.
No es solo optimizar el modelo
sino también el hardware mismo. Con un LED,
en teoría, se pueden "recortar" los
escenarios no deseados (otro entorno,
ambiente, etc.)
Colocar una iluminación que se designa como
iluminación constante.

En cuanto a la demo antes o durante la feria,
sabiendo cómo funca el modelo y predecir las condiciones,
busquemos generalizar el modelo para que se adapte.

Por ej.: la posición del plato tiene que estar marcada,
ya que quizás en una posición dada tenga mejor inferencia.

La idea no es que sea un modelo generalizado;
con tal de que identifique sus estados,
basta. No importa si lo llevo a donde
requiera; tengo la alimentación del plato,
está adecuada, etc.

Ese tipo de cosas pueden generar overfitting,
pero el $mu C$ debería arreglárselas.

#{
  set text(size: 16pt)
  $ "¡¡¡PRIORZAR EL DESARROLLO DEL PROYECTO DESDE AHORA!!!" $
}
