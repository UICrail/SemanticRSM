# Files: origin and licensing conditions

Please abide by the licensing conditions of the originators.


| file name                       | origin     | format     | notes                                                                                                                          |
| ------------------------------- | ---------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------ |
| advanced example railml.org.xml | RailOscope | railML 3.2 | Access granted by Torben Brand, Jernbanedirektoratet. Downloaded 12/11/2024. License: CC BY 4.0 for the purpose of MOTIONAL  . |
| Simple Example+RTC.xml          | RailOscope | railML 3.2 | See above. Export to railML 3.2 on RailOscope came with error messages.                                                        |
|                                 |            |            |                                                                                                                                |
|                                 |            |            |                                                                                                                                |

# Notes about railML 3.2 file contents

... and comparisons with sRSM.

## Presence of split Linear Elements

File "advanced examples..." shows that railML 3.2 allows linear elements to be split, resulting in chained Linear Elements. The RTM/RSM convention, also present in sRSM, is however to keep linear elements in one piece between track ends (buffers...) and convergence points (switches...), or between switches, in the MICRO case, a convention also applying to the other levels. Said more simply, the direct graph (dual of the line graph) has no nodes of degree = 2.

*For reference, sRSM introduces a single exception (using zero length linear elements to split between networks). An example is Linear Element with id=ne_55.*

This difference is a minor one, the RTM/RSM/sRSM convention not being a rule, but a recommendation for usage, the purpose of which is to promote that graphs produced by different entities about the same infrastructure are isomorphic, a definite plus for seamless data exchange.

The railML-to-sRSM transformation will join the split linear elements found. This will have an effect on all location data (spot, linear, area).

Since developing data transformers is possible but outstretching the MOTIONAL resources, we may avoid joining the split linear elements and may bypass steps 01 (split, not necessary anyway) and 02 (join) of the graph transformation.

## Composition Linear Elements

Still in the advanced example:

(to be completed)

# Handling of intrinsic coordinates

railML 3.2 intrinsic coordinates (ICs) as shown in the XSD play a role very similar to ports in sRSM : the ICs are elements and have an @id. ICs having value @intrinsicCoord = 0 or 1 are therefore functionally the exact equivalent of a port in RSM. In particular, two adjacent net elements in railML do not "share" an IC even though the coordinates of the ICs may coincide; ICs (as ports) denote extremities of different things; they are no "nodes" of the direct graph with a different name.

In the case of a composite net element, said element has its own IC "instances" coinciding with ICs of their components. See for instance the case of ne_ms_141. In the case of railML 3.2, the navigabilities have to be expressed. In the case of sRSM, navigabilities at higher levels (MESO...) can be expressed directly, but can also be derived from the MICRO level navigabilities (MESO level ports are owl:sameAs the corresponding MICRO level ports, even though their exact position may differ by a few centimeters...).

Unclear in railML: element ne_ms_141 has no length attribute, therefore probably not deemed linear (the XSD does not make that difference explicitly, it only knows about net elements, derived from the RTM class PositioningNetElement, superclass of linear and non-linear element). It has three ICs, with value 0, 0, 1 which seems actually linked with the linear referencing system (kilometric points), but it is not clear what the values tell and how they should be used.

By contrast, in sRSM, the ports are numbered lexically (by their identifiers), here: 0, 1, 2... The numbering is only there to help human readers. Intrinsic coordinates are only used in association with the metrics of linear elements.
