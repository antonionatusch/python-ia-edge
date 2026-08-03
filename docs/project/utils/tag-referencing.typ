#let ref_name(label) = context {
  let el = query(label).first()
  if el != none and el.func() == heading {
    link(el.location(), el.body)
  }
}
