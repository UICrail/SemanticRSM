"""
Assumes that the OSM data are in GeoJSON format.
"""

import geopandas as gpd
import rdflib
from rdflib import RDFS
from rdflib.namespace import RDF, Namespace
from shapely.geometry import LineString

# Define your namespaces
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
MY_NS = Namespace("http://www.example.org/osm#")
RSM = Namespace("http://www.example.org/rsm#")

# Initialize your RDF graph
g = rdflib.Graph()

# Load OSM data (converted to GeoJSON) with GeoPandas
gdf = gpd.read_file("~/PycharmProjects/SemanticRSM/Source data/OSM/Sankt_Pölten.geojson")

# Filter for railway lines if the dataset contains various types of data
railways = gdf['railway']

# Process railway lines
for index, row in railways.iterrows():
    line_uri = MY_NS[f"railway/{index}"]
    # Assuming 'geometry' is in WKT format; if not, convert it using shapely
    wkt = row['geometry'].to_wkt() if isinstance(row['geometry'], LineString) else str(row['geometry'])
    g.add((line_uri, RDF.type, RSM.LinearElement))
    g.add((line_uri, RDFS.subClassOf, GEO.Geometry))
    g.add((line_uri, GEO.asWKT, rdflib.Literal(wkt, datatype=GEO.wktLiteral)))

# Serialize the graph to a Turtle file
g.serialize(destination='osm_railways_output.ttl', format='turtle')
