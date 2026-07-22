#let apa-figure(
  body,
  note: none,
  specific-note: none,
  probability-note: none,
  ..args,
) = {
  figure(
    [
      #set par(first-line-indent: 0em)
      #body
      #set align(left)
      #if note != none [
        _Nota._
        #note
      ]
      #parbreak()
      #specific-note
      #parbreak()
      #probability-note
    ],
    ..args,
  )
}
