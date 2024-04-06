# SemanticRSM
RSM recast, based on direct RDF/OWL modelling.

RSM stands for Rail System Model. RSM is a UIC IRS (International Railway Standard), first released in 2016 as RailTopoModel (RTM): see https://rsm.uic.org.

## License
EUPL 1.2

## Purpose
RTM 1.0, RTM 1.1, RSM 1.2 and its extensions, all published by UIC, follow principles generally observed in conceptual modelling, using UML. RSM 1.2 model was successfully transformed into an OWL ontology, using the Ontorail toolset developed by UIC. However, the expressiveness of OWL differs from UML class diagrams. OWL offers possibilities to make RSM both more compact and more expressive, while remaining compatible with former, UML-based versions. The present repository summarizes the re-casting efforts.

## Design goals
* Backward compatibility.
* Simplification (not: dumbing down).
* Separation into small vocabularies (high-cohesion, low-dependency principle) to facilitate ontology management.
* Improvements:
    - about topology: navigability as a transitive property, internal navigability in "operational points" (yards, stations), more flexible composition of net elements...
* Systematic, explicit usage of well-established external vocabularies, where relevant: for instance, SSN ontology.
* Ability to determine paths under constraints using SPARQL and inference engines, rather than bespoke code.

## Design process
The process considers the RINF use case, with priority to topology and geographic referencing. However the design, as previously with RSM, emphasizes generality and avoids ad-hoc solutions.

Other use cases may come from other pieces of EU Law, such as TAF TSI, or from ongoing EU projects.

## Tools
* [Protégé](https://protege.stanford.edu/) desktop 5.x for RDF edition, checking, and saving to different formats.
* [EasyRdf](https://www.easyrdf.org/converter) for file conversion.
* Graphics:
    - Sparx Enterprise Architect for UML diagrams, possibly using the built-in [ODM](https://www.omg.org/odm/) UML profile.
    - Draw.io for hand-drawn graphics.
    - Diagrams (in the Wiki) were generated from an extended markdown using [Mermaid](https://github.com/mermaid-js/mermaid), or from ttl files using [OntoMermaid](https://github.com/floresbakker/OntoMermaid).
 
## Data
* Sample data sets:
    - based on fictive or real networks;
    - possibly generated from OpenStreetMap.

## Languages
RDF/[RDF-star](https://www.w3.org/2022/08/rdf-star-wg-charter/)/OWL/SHACL, SPARQL/SPARQL-star, Python, SWI Prolog.

# Documentation
## Railway network description: topology, its rationale, and related subjects
_This document is under preparation._

There is not a single way to formally describe networks. Nor are there "obvious" ways. Taking a step back from decade-long developments and discussions, we try to get back to some fundamental subjects.

## Wiki
The Wiki documents the design process, esp. main design choices. It is an integrated wiki; see menu bar.
