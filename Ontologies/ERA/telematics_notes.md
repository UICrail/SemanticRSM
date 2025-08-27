# About ERA Telematics Ontology

## Version considered
Revision: v6.0, published April 2025, downloaded August 2025. In the following, it is called "the ontology" when not ambiguous.

## URI

This ontology is

- documented on https://linkedvocabs.org/data/era-ontology/telematics/index-en.html
- downloadable as ttl file from https://linkedvocabs.org/data/era-ontology/telematics/ontology.ttl
- prefixed by @prefix : <http://data.europa.eu/949/>

## OWL2 compliance
The ontology uses xsd:time, while OWL2 does not support it (only xsd:datetime). Consequence is, HermiT reasoner will crash; Pellet reasoner won't take notice.

From a user perspective, xsd:time (time of the day, i.e. of any day) is a valid choice in the context of timetabling.

OWL2 is probably too restrictive here, since temporal algebra (such as Allen temporal algebra) is not built into OWL2.
The W3C time ontology defines such temporal properties and consequently uses xsd:date and xsd:datetime, but not xsd:time for which no total order can be defined.

In the present context, xsd:time usage is correct and should be kept.

## Imports and links, or absence thereof

### Not using W3C Time

The sensible use of xsd:time does not preclude the usage of W3C Time ontology where relevant.

### No link with infrastructure representation

The ontology can be called "standalone", in the sense that it does not import or reference other ERA ontologies such as "the ERA ontology" describing the infrastructure (topology, etc.). Also, we notice that the URI is the same for both vocabularies (http://data.europa.eu/949/). This raises several questions:

- how to link between spatial entities in the ERA telematics ontology (such as primary location codes, paths, etc.) and the underlying infrastructure elements (such as linear or area locations)?
- is it ERA intention to keep infra and telematics vocabularies separated but linked (with imports or references)? see also the general discussion about modularity in the context of the CDM.

### Re-defining units as annotations

While the ERA (infrastructure) vocabulary makes use of QUDT, this ontology redefines units with an annotation property (unitOfMeasure). This choice favours reasoner performance over semantic safety.

Given that 1) the infra ontology uses QUDT, and 2) in daily operations, the usage of reasoners is not very likely while data interoperability is of paramount importance, **this choice does not seem optimal**.

## Structure

### Flat structure, with exceptions

With very few exceptions, classes and properties are flat (no taxonomy).

The 4-tier hierarchy for the annotation properties is interesting (version 3_5 annotations include TAF TSI annotations include schemes annotations includes ERA annotations), but version 3_5 does not seem relevant in the context of the present version 6. Anyway it is not used.

Data properties have a "container" (a super-property called dataProperties, unfortunately in the plural which is not RDF or OWL convention, but XSD-like). For some reason, there is no symmetric container for all object properties or all classes. A single data property (:LocationSubsidiaryCode) escaped the container, for no apparent reason.

### Packages?

**Packaging them into several modules should be considered**, since the ontology is large (so was the XSD: more than 10000 lines) and the topics addressed are varied (see preliminary works under LinX4Rail).

### Code lists

List of codes for ReasonOfReference should be an enumeration, rather than a rdfs:comment. The form of the enumeration (owl:oneOf a list of named individuals, or a SKOS concept scheme, etc.) is another interesting subject where many options are offered.

### Time representation

Time is a class and the range of an object property hasTime. But Time has a functional data property Time (same label, and same upper case identifier and same URI).

## Documentation

Definitions (as rdfs:comment property values) are generally missing, although they are often provided in the source XSD. Maybe the import pipeline (using SHACL as an intermediate step) is to blame.

Definitions could have been conveyed using sh:description or rdfs:comment at that intermediate stage.

## Contents

[reserved]

