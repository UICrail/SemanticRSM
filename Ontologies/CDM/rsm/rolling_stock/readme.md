# Rolling stock mockup
## Purpose (see also Wiki)
This ontology intends to represent various __aspects__ of railway rolling stock, independently of each other:
1. train composition (coarse) : vehicles, vehicle rakes, trainsets... => defined under "rolling stock typology"
2. train composition (detailed) : sequence and orientation of vehicles in a formation => in preparation
3. rolling stock components : axles, wheels, couplers, brake pads... => in preparation
4. typology : locomotive, coach, wagon, EMU,... => defined under "rolling stock typology" 
5. payloads : passengers, freight, containers... => referenced under "rolling stock typology", to be defined (as property sets) in another vocabulary
6. performance settings : effort vs. speed curves (traction and braking), resistance to forward movement, mass and rotating mass inertia ... => in preparation
7. geometry : "the left axle box of 2nd axle of wagon number 12345678 is 346m from the front of this running train and 45cm above top of rail", of interest for en route diagnosis => in preparation

See integrated wiki for further explanations.

The above aspects are made available at various business __levels__:
1. operations planning : "train IC94 is composed of three first-class, one dining, and seven second-class coaches, hauled by an electric locomotive"
2. manufacturing : "to serve ICxx trains, these are manufacturer Y catalogue entries (rolling stock types, in the sense of EU law): ..."
3. fleet inventory : reflecting actual vehicles or trainsets with a "chassis number" and/or an EVN.

These "levels" and their relationships are illustrated in the "rolling stock level" vocabulary.

Design goals are:
* each aspect and level shall be pairwise independent of others, as far as possible;
* each level will be able to document relevant aspects; operation planning will be less detailed, manufacturing (type) level much more so, and fleet inventory level even more so; 
* each level will document its compatibility with a higher level, e.g. fitness of a manufactured type with respect to operational requirements, or conformity of a delivered vehicle with its type specifications;
* the ontology user will be able to freely combine, for each use case, the relevant set of aspects with the relevant set of levels;
* the ontology shall be kept minimal and open to extensions, in order to serve use cases not listed;
* the use cases contributing to the "core" of the ontology will be decided in the course of the MOTIONAL project.
