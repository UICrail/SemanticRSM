# SemanticRSM
RSM recast, based on direct RDF/OWL modelling

## License
The indicated license is provisional. It should be EUPL 1.2, which is not currently available in the dropdown list. To be confirmed.

## Purpose
RTM 1.0, RTM 1.1, and RSM 1.2 follow principles generally observed in object-oriented modelling, using UML. RSM 1.2 model was successfully transformed into an OWL ontology, using the Ontorail toolset developed by UIC. However, the expressiveness of OWL differs from UML class diagrams. OWL offers possibilities to make RSM both more compact and more expressive, while remaining compatible with former, UML-based versions. The present repository summarizes the re-casting efforts.

## Design goals
* Backward compatibility.
* Simplification.
* Ability to determine paths under constraints using SPARQL and inference engines, rather than bespoke code.
