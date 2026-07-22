#let setup_page(
  project_short_name: str,
  body,
) = {
  set page(
    footer: context {
      align(right)[#counter(page).display("1")]
    },
    header: context {
      block(width: 100%)[
        #set par(leading: 0.65em)
        #project_short_name
      ]
      v(-0.5em)
      line(length: 100%, stroke: 0.5pt)
    },
  )
  body
}
