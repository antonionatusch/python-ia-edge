#set text(lang: "es")
#align(center)[
  = Clase 13: Herramientas de ML/DL
  = 20/07/2026
]

= Antes de la clase
Preguntó sobre el proyecto
y otras cosas.

También
sobre las tareas de ML y DL para subirlas.

Nos comentó que habló con los administrativos
de TechLab e indicó que la feria
será en un ambiente de la SIB
en La Paz. Los que no vayamos
a La Paz tenemos que subir un video.
La idea es que la feria sea el
sábado primero de agosto
(01/08/2026)

En base a la calificación del proyecto
se nos hará la entrega del certificado.

En la clase de hoy, vamos a hacer un repaso.

= Antecedentes históricos de ML
Un hito importante fue la publicación
de varios algoritmos nuevos de detección
de rostros.
Antes de estos algoritmos,
se usaba LBPH.

Según #link("https://share.google/aimode/6enyu7fKJFb0kbvFl")[Google Modo IA]:

*#align(center)[
  "LBPH (Local Binary Patterns Histograms) es un algoritmo de reconocimiento facial sencillo pero altamente efectivo. Funciona extrayendo los patrones de textura del rostro de una imagen y creando un histograma que luego se compara con los rostros entrenados para identificar a una persona".
]*

Favorece ambientes de computación no muy potentes,
y sirve si es que no necesitamos detectar
la cualidad tridimensional de una cara.

En el caso de los filtros, suelen hacer una suma con
la imagen subyacente.

En esta clase, vamos a ver la forma de hacerlo
funcionar.

A diferencia de una ANN, en este caso,
las épocas dependen de la cantidad de fotos.

= Sobre ESP-DL
Es una biblioteca de DL dedicadas a los SoC (system on a chip)
de Espressif.

= Sobre el código de las capturas, al crear un dataset
Un error común es colocar fondos muy variados.
Se recomienda que haya un 30 % de fondos coloridos
y un 70 % de fondos constantes.

= Sobre RoboFlow
No solo tiene datasets y modelos,
sino también ayuda a crear datasets
y otras cosas. Además, soporta programación
agéntica.

= Código Python en clases, captura de fotos para reconocimiento de rostros con MediaPipe
== Captura fotos
#let python-code-class = read("../../../modulo-3/clase-13/clase13capturaref.py")

#raw(python-code-class, lang: "python", block: true)

== Entrenamiento
#let python-code-class = read("../../../modulo-3/clase-13/clase13train.py")

#raw(python-code-class, lang: "python", block: true)

== Prueba
#let python-code-class = read("../../../modulo-3/clase-13/clase13test.py")

#raw(python-code-class, lang: "python", block: true)

`TODO: adjuntar código .ino y
el script de los filtros`

= Comentarios extra fuera del tema
== Sobre parámetros/umbrales
Mencionó límites relacionados a los vistos
de la anterior clase. Tiene que ver con
el uso de la memoria y eso.

== Sobre la presentación del 22 de julio
Lo vamos a ver en clase después de una partecita
teórica.
