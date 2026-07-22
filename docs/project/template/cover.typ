#let tab = h(2em)
#let cover_page(
  techlab_logo: str,
  student_full_name: str,
  course_full_name: str,
  edge_img: str,
  project_name: str,
  professor_name: str,
) = {
  page(footer: none, numbering: none)[
    #align(center + horizon)[
      #image(techlab_logo, width: 25%)
      #v(1em)
      #text(size: 12pt, weight: "bold")[Academia Tech Lab Bolivia]
      #v(1em)
      #image(edge_img, width: 25%)
      #v(1em)

      #text(size: 12pt)[*#project_name*]
      #v(1.5em)

      // Invisible grid keeps metadata perfectly aligned
      #align(center)[
        #block(width: 65%)[
          #grid(
            columns: (70pt, 1fr),
            // Space allocated for labels vs data
            row-gutter: 1.2em,
            // Space between lines
            align: (left, left),
            // Ensures text within cells stays left-aligned
            [*Curso:*], [#course_full_name],
            [*Instructor:*], [#professor_name],
            [*Estudiante:*], [#student_full_name],
          )
        ]
      ]

      #v(2em)

      #align(bottom)[Mayo 2026]
    ]
  ]
}
