## Versions
Version 3.1.2 (file Era_ontology_312.ttl), released on 27/6/2025 was downloaded from https://data-interop.era.europa.eu/era-vocabulary/.

**Ontology version IRI is missing.** 

## OWL2 and reasoner compatibility

ERA ontology 3.1.2 uses xs:date, which is not supported by OWL 2. In practice, use the Pellet reasoner that is less strict than HermiT.

## Vocabularies used but not mentioned

The ERA ontology depends on various other vocabularies, but dependencies are not very explicit. There are no owl:import axioms and only a few @prefix statements. Following vocabularies appear in URIs but have no corresponding prefixes:

| URI Stem                             | Occurrences | Vocabulary/Standard                         |
| ------------------------------------ | :---------: | ------------------------------------------- |
| http://creativecommons.org/ns#       |      2      | Creative Commons Rights Expression          |
| http://purl.org/dc/terms/            |    1539     | Dublin Core Terms                           |
| http://xmlns.com/foaf/0.1/           |     14      | FOAF (Friend of a Friend)                   |
| http://www.w3.org/ns/org#            |     12      | W3C Organization Ontology                   |
| http://www.w3.org/2004/02/skos/core# |     423     | SKOS (Simple Knowledge Organization System) |
| http://qudt.org/vocab/unit/          |     72      | QUDT units vocabulary                       |

Of course, using full URIs as literals is legal under RDF and OWL2.

**Readability and maintainability would be improved by using prefixes for the above**. This is especially true for QUDT, the usage of which is not commonplace.