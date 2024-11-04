# Purpose

Pick an OSM geojson file and transform it into an RSM-compliant topology.ttl graph

# Data sources

The source of the OSM file can be OpenStreetMap (using overpass turbo for instance) or a schematic representation
of the network by means of draw.io.
The resulting graph will be stored in the Output_files/Intermediate_files folder.

# Processing steps

The transformation is handled by full_transformation.py. It first uses the **file transformation** module osm_geojson_to_ttl.py (see Import/OSM_import folder), then calls the **graph transformation** modules step0x_... in a sequence.
