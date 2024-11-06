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

## General principles

The network is represented in 2D as a set of track segments. The following conventions apply:

* a network is composed of track segments. These shall be represented, in drawIO, by lines (line segments), with or without waypoints.
  * we recommend using waypoints to give the drawing a realistic aspect while keeping the drafting simple and effective.
  * at the time of writing, the processing of waypoints is not yet finished.
* each track segment is a __linear element__ in the sense of sRSM, i.e. it should start and end at a switch, crossing (where 3 or 4 track segments converge) or into nothing (where you would have a buffer for instance).
* use __snap to grid__ to join linear elements. The program will identify connections between extremities of linear elements by identity of coordinates, rather than vicinity.
* you can approximate a curve by having chained track segments. You may also use a curve instead.
* chained track segments will be interpreted as a single linear element in RSM.
* track segments _should_ be identified by a label (in draw.io, double-click on the segment for input).
  * unlabeled segments will receive an empty label (empty string)
  * if track segments are chained, only one segment needs to be labeled, and the label will be passed onto the linear element.
  * if chained track segments have the same label, this label will also be applied to the resulting linear element
  * if chained track segments have different labels, these will be concatenated to yield the label of the linear element
* track segments can only be connected at their extremities. You cannot have a track segment branching out from the "middle" of another one.
* track segments can cross, but this will be interpreted as a over- or underpass, not as a crossing. To represent a crossing (diamond crossing, etc.), use 4 convergent segments.
* track segments _may_ be terminated by arrows (choose symbols accordingly). The arrows are only helping visualize where segments start or end, and help telling crossings and flyovers apart. Orientation is ignored.
* to represent a siding along a straight track, you may use for instance three aligned, straight segments, and one curved segment. Parallelism is not important, but visually, the siding should be one the one or the other side of the "through" track, and the graphical representation is expected to show where the "toe" and "heel" side of the switch is situated.

## Dealing with (diamond | single slip | double slip) crossings

_FR: traversées simples, traversées jonctions simples ou doubles; DE: Kreuzung resp. einfache - resp. doppelte Kreuzungsweiche_

In the case of crossings, additional information is needed to distinguish between diamond / single slip / double slip crossings.
Lacking such info, the user may choose to default all crossings to either double switch crossing or diamond crossing type (default option in the code).

In any case, a crossing is defined where exactly four linear elements converge at their extremities.

WARNING: Two intersecting track segments in the drawing will be intepreted as a flyover.

# Methodology

The drawIO import rests on the conversion of the drawIO XML file into an OSM file in GeoJSON format.
Additional processing rests on:

* the input geometry,
* conventional annotations on the diagram.

# Libraries

## XML parsing

We use lxml and xmltodict, which does not catch all XML info but is sufficient in the present case.

## Geometry

We use geopandas and shapely, essentially to find nearest objects and projected coordinates (example: a trackside signal should find its track; a slip crossing annotation should find its crossing ).
For coordinate conversions: pyproj

## Shortcomings of drawIO

The SVG output could also be used, but would involve more refined coding:

* Unlike the XML output, the SVG output will not guarantee that segment extremities snapped to the (canvas) grid will have the same coordinates.
* In addition, the structure of the SVG file varies from one segment to another, for no apparent reason.

However the display of the SVG files in a browser (Firefox was used for testing) looks fine.
