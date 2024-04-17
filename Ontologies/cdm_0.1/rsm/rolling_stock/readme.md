# Rolling stock mockup
## Purpose
This ontology intends to represent "static" __aspects__ of railway rolling stock, independently of each other:
1. train composition : vehicles, vehicle rakes, trainsets...
2. rolling stock components : axles, wheels, couplers, brake pads...
3. typology : locomotive, coach, wagon, EMU,...
4. payloads : passengers, freight, containers...
5. performance settings : effort vs. speed curves, resistance to forward movement, mass and rotating mass inertia ...

(under preparation) The above aspects are made available at various business __levels__:
1. operations planning : "train IC94 is composed of three first-class, one dining, and seven second-class coaches, hauled by an electric locomotive"
2. manufacturing : "to serve IC trains, these are manufacturer X catalogue entries (rolling stock types, in the sense of EU law)"
3. fleet management : reflecting actual vehicles or trainsets with a "chassis number" such as an EVN.

Design goals are:
* each aspect and level shall be pairwise independent from others, as far as possible;
* the ontology user will be able to freely combine, for each use case, the relevant set of aspects with the relevant set of levels;
* the ontology shall be kept minimal and open to extensions, in order to serve use cases;
* the use cases contributing to the "core" of the ontology will be decided in the course of the MOTIONAL project.