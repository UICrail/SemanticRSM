# Purpose

Pick a geojson file and transform it into an RSM-compliant topology.ttl graph

# Data sources

The source of the geojson file can be OpenStreetMap (using overpass turbo for instance) or a schematic representation
of the network by means of draw.io.
The resulting graph will be stored in the Output_files/Intermediate_files folder.

# Processing steps

Depending on the origin of the data, geojson file uses tags to indicate how the tagged elements should be treated.

The transformation is handled by full_transformation.py. It first uses the **file transformation** module osm_geojson_to_ttl.py (see Import/OSM_import folder), then calls the **graph transformation** modules step0x_... in a sequence.

The steps consist in:

1. splitting linear elements if need be (case of linear elements crossing each other, or linear elements having branches between their extremities).
2. joining consecutive linear elements into single linear elements, stretching from a junction to the next.
3. adding ports corresponding to the extremities of linear elements.
4. (a) adding connexity and navigability properties to ports; (b) dealing with slip switches (slip crossings).
5. dealing with meso elements and their ports (under preparation).