# About European Union Agency for Railways, ERA Telematics Ontology. Revision: v6.0.
## OWL2 compliance
The ontology uses xsd:time, while OWL2 does not support it (only xsd:datetime). Consequence is, HermiT reasoner will crash; Pellet won't take notice.

Using xsd:time (time of the day, i.e. of any day) is valid in the context of timetabling. OWL2 is probably too restrictive here, since time algebra is not built into OWL2f.
