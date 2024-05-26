# Imports GeoJSON file using GeoPandas
# WARNING: does not seem to work properly with GeoJSON export from OSM using the Overpass API;
# overlapping linestrings would cause trouble in the subsequent processing.

import geopandas as gpd
import rdflib
from rdflib import RDF, Literal, RDFS
from shapely.geometry import LineString, Point

from Code.Namespaces import *


def osm_import(osm_file_path: str, short_name: str = "", linear_element_prefix: str = 'rwy',
               geometry_prefix: str = 'geom', with_properties: bool = True):
    """

    :param geometry_prefix:
    :param linear_element_prefix:
    :param osm_file_path:
    :param short_name: will be used for the intermediate and final file naming
    :param with_properties: if False, geometries will not be associated with the linear elements via hasNominalGeometry.
    In such case, only the URIs will tell which linear element matches which geometry.
    :return: None (a file is created)
    """
    # Initialize RDF graph
    g = rdflib.Graph()

    # Bind the namespaces
    g.bind("geo", GEOSPARQL)
    g.bind("rsm", RSM_TOPOLOGY)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("rsm", RSM_GEOSPARQL_ADAPTER)
    g.bind("", WORK)

    # Load OSM data (assumed to be in GeoJSON format) with GeoPandas
    gdf = gpd.read_file(osm_file_path)

    # Assuming the 'railway' attribute is within the properties field, filter for railway lines
    railways = gdf[gdf['railway'] == 'rail']  # tagged value 'rail' designates a track

    # Process railway lines
    for index, row in railways.iterrows():
        line_uri = WORK[f"{linear_element_prefix}_{index}"]
        geom_uri = WORK[f"{geometry_prefix}_{index}"]
        # Convert geometry to WKT
        if isinstance(row.geometry, LineString) or isinstance(row.geometry, Point):
            wkt = row.geometry.wkt
        else:
            wkt = str(row.geometry)

        g.add((line_uri, RDF.type, RSM_TOPOLOGY.LinearElement))
        if with_properties:
            g.add((line_uri, RSM_GEOSPARQL_ADAPTER.hasNominalGeometry, geom_uri))
        g.add((geom_uri, RDF.type, RSM_GEOSPARQL_ADAPTER.Geometry))
        g.add((geom_uri, GEOSPARQL.asWKT, Literal(wkt, datatype=GEOSPARQL.wktLiteral)))

    # Serialize the graph to a Turtle file
    g.serialize(
        destination=f'/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{short_name}_raw.ttl',
        format='turtle')
