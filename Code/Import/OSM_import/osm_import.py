import geopandas as gpd
import rdflib
from rdflib import RDF, Literal
from rdflib.namespace import Namespace
from shapely.geometry import LineString, Point

# Define your namespaces
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
MY_NS = Namespace("http://www.example.org/osm#")
RSM = Namespace("http://www.example.org/rsm#")

def osm_import(osm_file_path):

    # Initialize your RDF graph
    g = rdflib.Graph()

    # Load your OSM data (assumed to be in GeoJSON format) with GeoPandas
    gdf = gpd.read_file(osm_file_path)

    # Assuming the 'railway' attribute is within the properties field, filter for railway lines
    railways = gdf[gdf['railway'] == 'rail']

    # Process railway lines
    for index, row in railways.iterrows():
        line_uri = MY_NS[f"railway/{index}"]
        # Convert geometry to WKT
        if isinstance(row.geometry, LineString) or isinstance(row.geometry, Point):
            wkt = row.geometry.wkt
        else:
            wkt = str(row.geometry)

        g.add((line_uri, RDF.type, RSM.LinearElement))
        g.add((line_uri, RDF.type, GEO.Geometry))
        g.add((line_uri, GEO.asWKT, Literal(wkt, datatype=GEO.wktLiteral)))

    # Serialize the graph to a Turtle file
    g.serialize(destination='/Users/airymagnien/PycharmProjects/SemanticRSM/Intermediate_files/osm_railways_raw.ttl', format='turtle')
