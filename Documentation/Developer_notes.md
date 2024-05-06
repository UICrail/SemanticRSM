# About inferred properties

RDFLIB only takes into account stated properties, not however inferred properties.
Consequently, symmetry and transitivity cannot be exploited unless:
* inferred properties are added in the course of the processing (and possibly removed afterwards), or
* an inference engine or a SPARQL endpoint is called to the rescue, or
* [Owl2ready](https://pypi.org/project/owlready2/) is used instead of rdflib