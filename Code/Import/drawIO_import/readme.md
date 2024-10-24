-- dummy change for GitHub testing --

# Purpose
Let the user draw a simple network using draw.io.

The software will derive the network representation as an RDF/OWL ontology, using sRSM (semanticRSM) or similar ontologies.

The RDF representation can then be exported to an RDF Turtle file (or other formats), in order to be loaded, checked, and manipulated in Protégé for instance.

# Limitations
Only for pedagogic purposes, demos, etc.

# Ontologies
The user may select between ontology vocabulary versions.

# Using draw.io as input interface
The network is represented in 2D as a set of track segments. The following conventions apply:
* each track segment is a linear element in the sense of sRSM, i.e. it should start and end at a switch, crossing (where 3 or 4 track segments converge) or into nothing (where you would have a buffer for instance).
* use snap to grid to join linear elements. The program will identify connections between extremities of linear elements by identity of coordinates, rather than vicinity.
* you are allowed, but should avoid, to have chained track segments: while sRSM-compatible, this is not standard sRSM usage.
* track segments can only be connected at their extremities. You cannot have a track segment branching out from the "middle" of another one.
* track segments should be terminated by arrows (choose symbols accordingly). The arrows are only helping visualize where segments start or end. Orientation is ignored.
* track segments should be identified by a label (double-click on the segment for input)
  * unlabeled segments will receive a "random" identifier
* to represent a siding along a straight track, you may use for instance three aligned, straight segments, and one curved segment. Parallelism is not important, but visually, the siding should be one the one or the other side of the "through" track, and the graphical representation is expected to show where the "toe" and "heel" side of the switch is situated.
* in the case of crossings, additional information is needed to distinguish between diamond / single slip / double slip crossings: to be defined.
  * meanwhile, the user will have to choose between "all diamond" and "all double slip".
  * two intersecting track segments will be treated as a flyover.

# Methodology
The drawIO import rests on the conversion of the drawIO XML file into an OSM (native format) file.
Some additional processing rests on the input geometry, allowing additional input into the RDF file (the intermediate OSM file does not get involved).

# Libraries
## XML parsing
We use xmltodict, which does not catch all XML info but is sufficient in the present case.

## Geometry
We use shapely, essentially to find nearest objects and projected coordinates (example: a trackside signal should find its track; a slip crossing annotation should find its crossing ).

