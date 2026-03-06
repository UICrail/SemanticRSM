# SemanticRSM

**SemanticRSM** is a semantic reinterpretation of **UIC's Rail System Model (RSM)** based on direct **RDF/OWL modeling**.

The project revisits the original RSM conceptual model and expresses it natively using Semantic Web technologies, enabling its use in **knowledge graph environments** while remaining compatible with previous UML-based versions.

---

# Relationship with RSM and RTM

RSM (Rail System Model) is an evolution of an **UIC International Railway Standard (IRS)** originally released in 2016 under the name **RailTopoModel (RTM)**.

RTM and subsequent RSM versions were defined using **UML conceptual modeling**, following widely accepted conceptual modeling principles.

The SemanticRSM project revisits these models and represents them directly in **RDF/OWL**, taking advantage of the expressive capabilities of Semantic Web technologies.

More information about the RSM standard can be found at:

https://rsm.uic.org

---

# Purpose

Previous work successfully transformed **RSM 1.2 UML models into OWL ontologies** using the Ontorail toolset developed by UIC.

However, **OWL has different modeling capabilities than UML class diagrams**.

When used directly rather than through automated translation, OWL enables models that are:

- more compact
- more expressive
- more suitable for semantic reasoning

SemanticRSM therefore represents a **native OWL reinterpretation of RSM**, designed to preserve compatibility with previous UML-based models while improving semantic expressiveness.

---

# Design goals

The project follows several guiding principles.

### Backward compatibility

Data conforming to earlier RTM or RSM versions should be convertible with minimal effort, enabling automated transformation where possible.

### Simplification

The goal is **simplification without loss of meaning**, taking advantage of OWL expressiveness to remove unnecessary modeling complexity.

### Modular ontology structure

The model is divided into **small, coherent vocabularies** following the principle:

> high cohesion, low dependency

This facilitates ontology maintenance and reuse.

### Improvements to topology modeling

Several enhancements have been introduced compared with earlier UML models:

- navigability expressed as a **transitive property**
- internal navigability within non-linear elements such as **stations and yards**
- more flexible composition of **network elements**

### Reuse of established vocabularies

Where relevant, SemanticRSM relies on widely adopted ontologies, including:

- **SOSA / SSN**
- **GeoSPARQL**
- **W3C Time**
- ontologies for **quantities and units**

This improves interoperability with other semantic models.

### Reasoning-based path computation

The model allows **path determination under constraints** using:

- SPARQL queries
- inference engines

Dedicated algorithms may still be preferable for performance reasons in operational systems.

---

# Design inputs

The design of SemanticRSM is influenced by several practical use cases and initiatives.

Key inputs include:

- the **RINF (Register of Infrastructure)** use case, with emphasis on micro-level topology and geographic referencing
- **System Pillar requirements** related to rolling stock typology
- **FP5 TRANSF4M-R** requirements concerning the description of infrastructure “last mile” and rolling stock defects
- other **FPx MOTIONAL** initiatives

Relevant concepts may also originate from **European railway legislation**, such as **TAF TSI**, or from ongoing EU research projects.

Despite these inputs, the model prioritizes **generality and long-term usability**, avoiding ad-hoc solutions.

---

# Demonstrations

Two demonstration workflows illustrate the generation of SemanticRSM data:

- generating an RDF/Turtle representation from a **schematic track plan** created in draw.io
- generating SemanticRSM data from **OpenStreetMap queries**

The demonstrations are available in the **Flask** folder.

To run the demo server locally:
