# About topology and navigabilities

## Topology definition

Our context is the railway "iron" network topology. Topology is about the function "guiding the rolling stock", exclusively. This means that topology is not about other functions such as "protect rolling stock from collisions with other rolling stock" or "provide passenger services".

Other functions, such as "conveying [electric traction] energy", may also give rise to distinct topologies: for instance, electrical networks can be represented as nodes (or junctions) and branches, and this formalism was theorised by Gustav Kirchhoff already in 1845.

## Topology scope

While topology models could be generalized to other subsystems like, precisely, "energy" (electric tractive energy supply, in full), we do not further investigate this path for the time being. This is because railways are a guided transport system, and nearly every subsystem can be put in relation with the "iron network" (tracks, etc.). Consequently, network topology is of special importance.

One subsystem for which the "iron network" topology is largely irrelevant is PRM. Accessible paths in and around stations have nothing to do with rails. However, other similar models have been proposed and standardized for that purpose.

The topology model could certainly be extended to the energy subsystem. Energy network description models exist, and are at the basis of functional energy models that are out of our scope.

## Topology presented as a graph

### Nodes: track sections

As rolling stock in operations rests on tracks, and always has the possibility to mode along a track, it seems natural (from the point of view of graph theory) to defined track sections as graph nodes.

This is also natural from a railway operations point of view: a driver starts his mission from, typically, some service track; passenger train 714 will originate at King's Cross station, track 9 3/4, etc.

### Edges: links between track sections

Consequence of the above is, edges would describe available links between track sections. In fact, the nature of the links will also define the track sectioning. This is why definitions are essential.

A link would be, for instance, two track sections, A and B, abutted to each other at one of their extremities. In such case, a vehicle could run from A to B (and conversely). However, it is generally not useful to have to track sections in such a simple case: the union of A and B still qualifies for being called a track section where the vehicle may run unhindered, and can be considered a single node. In graph theory, this merging would be called a contraction.

The situation gets more interesting when three track sections converge: for instance, a switch with one incoming track and two outgoing tracks, one "through" and one "diverted". Since we are not interested in geometry or permitted speeds here, we can temporarily forget about the difference between through and diverted, but not "incoming".

One fundamental difference is that the incoming track section may give access to the two others, but running from "through" to "diverted" (and conversely) is not possible without stopping and reversing on the incoming track. In operations, stopping and reversing may be allowed (stopping and reversing at the driver's initiative only happens on service tracks). But *functionally*, the rolling stock *cannot* be guided from "through" to "diverted", nor from "diverted" to "through"; in both cases, transiting through "incoming" is *necessary*.

Note the expression "may give access": guiding the rolling stock from A to B is a function that may see many restrictions, including but not limited to the position of switch blades, the blade lock being established, maybe a signal being open, etc. Here, we do not consider any particular restriction, **not even the blade position, which is not a sufficient condition anyway**.

Since the topology documents the function "guiding the rolling stock", track sections as graph nodes *must* (not: *may*) end at such places where three or more sections would converge.

The graph edges, i.e. the links between nodes, are conventionally named "navigability", the links between tracksections.



## Mapping real world entities to topology elements

Graphs are mathematical abstractions of networks. Graph elements (nodes and edges) are supposed to match entities in the field, but the matching is a matter of conventions. A formal convention could be called a mapping. A mapping can be one-to-one.

### Track Section [entity] and Linear Element [topology]

An isolated track section would be abstracted by its centreline (halfway between rails, at the height of the top of the rails) because this is usually the reference line when it comes to guiding the rolling stock. Please note that this centreline is a 3D curve, with multiple geometries (as drawn, as delivered), and evolving in time due to track deformation and wear & tear. The next level of abstraction consists in forgetting about the geometry of the centerline, only considering that is is linear (a fully ordered set of contiguous locations in space, with two ends). A linear element is nothing more.

This is what makes topology useful as an abstraction: it varies less often, for instance when a branch line gets added to serve an industrial site, or when a station track plan is rationalised. Otherwise topology (a set of nodes and edges) remains stable, which is why it may be used as a reference for describing other system components. Wear & tear, geometry changes, length changes, all do not change a particular linear element. Not even changes in navigabilities would affect it directly , as navigabilities are only expressing relations with other linear elements.

### The case for switches

The most controversial aspect of the graph representation is, switches need not be nodes, unlike track sections: switches are merely devices that will realise the guiding function. As a matter of fact, one could represent the are around a switch with any of the two following graphs:

* three converging track sections with one "coinciding" point
* three converging track sections ending up in three different points of a switch

Both representations are equally valid, and can be represented using the topology graph described in the previous section.









## Navigability as a relation

### Navigability is directed

Navigabilities are **directed** edges (in the sense of graph theory), that we would represent as arrows between nodes (track sections). In general, the possibility moving from track section A to track section B entails the possibility of moving from B to A. So having a directed graph may seem superfluous. There are exceptions though: think of sprung switches (often used in stations along single track lines). If you think these are antiques, think otherwise: nowadays, springs sometimes get replaced by sensors and actuators. The implementation changes, the functionality is still asked for.

Seen as a relation (or an object property, in ontology parlance), navigability is not a symmetric relation (A to B is navigable does not imply that B to A is navigable, as there are exceptions). Nor is it antisymmetric (it may be the case that A to B is navigable and B to A too, as this is most often the case).

### Navigability is transitive - is it?

"If a vehicle can be guided from A to B and then from B to C, then it can be guided from A to C" is equivalent to "the 'guides rolling stock' relation is transitive". If stopping and reversing is possible, then navigability is transitive for sure: navigability merely expresses that track sections are somehow connected, regardless of the way of running. This is not the initial intent when expressing the function "guiding the rolling stock".







### 

