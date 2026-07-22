#import "template/imports.typ": *
#import "segments/work-proposal.typ": *
#import "segments/work-objective.typ": *
#import "segments/solution-method.typ": *
#import "segments/project-content.typ": *
#import "segments/about-development.typ": *
#import "segments/key-screens-screenshots.typ": *
#import "segments/architecture-description.typ": *
#import "segments/architecture-diagram.typ": *
#import "segments/code-snippets.typ": *
#import "segments/conclusions.typ": *
#import "segments/recommendations.typ": *

#show figure.where(kind: raw): set figure(placement: none)
#show figure.where(kind: raw): set block(breakable: true, sticky: false)
#show figure.where(kind: raw): set raw(block: true)
#show figure.caption: set align(left)
#show figure: set figure.caption(position: top)
#show figure.where(kind: image): set block(breakable: true, sticky: true)
#show figure.where(kind: table): set block(breakable: true, sticky: false)
#show figure.where(kind: math.equation): set figure(supplement: [Formula])
#show heading: set block(above: 1.5em, below: 1.5em)
#show heading: set text(size: 12pt, weight: "bold")
#show figure.caption: it => {
  strong[#it.supplement #context it.counter.display(it.numbering)]
  parbreak()
  emph(it.body)
}

#set figure.caption(separator: parbreak(), position: top)
#set par(
  leading: 1.5em, // Space between lines (double spacing)
  spacing: 1.5em, // Space between paragraphs
)

#set heading(numbering: "1.1.")
#set text(lang: "es", size: 12pt, font: "TeX Gyre Termes")

#set page("us-letter")


#cover_page(
  techlab_logo: TECHLAB_LOGO,
  student_full_name: STUDENT_FULL_NAME,
  course_full_name: COURSE_FULL_NAME,
  edge_img: EDGE_IMG,
  project_name: PROJECT_NAME,
  professor_name: PROFESSOR_NAME,
)

#pagebreak()
*Introducción*

El presente proyecto muestra un sistema de monitoreo inteligente motivado
por la necesidad personal de alimentar a mis mascotas.
Si bien existen alimentadores inteligentes, como los de Nexxt
Solutions Home #cite(<AboutNexxtSolutionsHome>, form: "prose"),
pocos incorporan monitoreo visual capaz de verificar la presencia real
de alimento y detectar fallos de dispensación.

#pagebreak()
#counter(page).update(1)
#set page(
  header: none,
  footer: context {
    align(right)[#counter(page).display("i")]
  },
)
#outline()

#pagebreak()
#counter(page).update(1)
#show: setup_page.with(
  project_short_name: PROJECT_SHORT_NAME,
)

= Planteamiento del trabajo
#work_proposal
#pagebreak()
= Objetivo del trabajo
#work_objective
= Método de solución
#solution_method
#pagebreak()
= Contenido del proyecto
#project_content
= Desarrollo
#about_development

#pagebreak()
== Arquitectura del prototipo
=== Descripción general de hardware y software
#architecture_description
=== Diagrama resumen de arquitectura
#architecture_diagram

#pagebreak()
== Capturas de pantalla de pantallas clave
#key_screens_screenshots

#pagebreak()
== Fragmentos de código
#code_snippets
= Conclusiones
#conclusions
= Recomendaciones
#recommendations

#pagebreak()
#set page(numbering: none)
#show bibliography: set heading(outlined: false)
#bibliography("references/references.yaml", style: "/assets/source/apa.csl")
