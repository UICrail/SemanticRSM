# Imports GeoJSON file using GeoPandas
# WARNING: does not seem to work properly with GeoJSON export from OSM using the Overpass API;
# overlapping linestrings would cause trouble in the subsequent processing.
import os.path

import geopandas as gpd
import rdflib
from rdflib import RDF, Literal, RDFS, OWL, DC
from shapely.geometry import LineString, Point

from Code.Namespaces import *
from Graph_transformation.full_transformation import OUTPUT_FOLDER


def initialize_rdf_graph():
    g = rdflib.Graph()
    g.bind("geo", GEOSPARQL)
    g.bind("rsm", RSM_TOPOLOGY)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("rsm", RSM_GEOSPARQL_ADAPTER)
    g.bind("", WORK)
    return g


def process_geometry(row):
    if isinstance(row.geometry, (LineString, Point)):
        return row.geometry.wkt
    return str(row.geometry)


def osm_to_ttl(osm_file_path: str, short_name: str = "", base_path: str = OUTPUT_FOLDER,
               linear_element_prefix: str = 'line',
               geometry_prefix: str = 'geom', with_geometry: bool = True):
    """

    :param base_path:
    :param geometry_prefix:
    :param linear_element_prefix:
    :param osm_file_path:
    :param short_name: will be used for the intermediate and final file naming
    :param with_geometry: if False, geometries will not be associated with the linear elements via hasNominalGeometry.
    In such case, only the URIs will tell which linear element matches which geometry.
    :return: None (a file is created)
    """

    # Initialize RDF graph
    graph = initialize_rdf_graph()

    # Load OSM data (assumed to be in GeoJSON format) with GeoPandas
    gdf = gpd.read_file(osm_file_path)

    # Assuming the 'railway' attribute is within the properties field, filter for railway lines
    railways = gdf[gdf['railway'] == 'rail']  # tagged value 'rail' designates a track

    # Add ontology name and other annotations
    graph.add((WORK[''], RDF.type, OWL.Ontology))
    graph.add((WORK[''], RDFS.label, Literal(short_name, lang='en')))
    graph.add((WORK[''], DC.creator, Literal("sRSM Flask App")))

    # Process railway lines
    for index, row in railways.iterrows():
        line_uri = WORK[f"{linear_element_prefix}_{index}"]
        geom_uri = WORK[f"{geometry_prefix}_{index}"]
        # Convert geometry to WKT
        wkt = process_geometry(row)

        graph.add((line_uri, RDF.type, RSM_TOPOLOGY.LinearElement))

        if label := row.get('label'):
            graph.add((line_uri, RDFS.label, Literal(label)))
        if with_geometry:
            graph.add((line_uri, RSM_GEOSPARQL_ADAPTER.hasNominalGeometry, geom_uri))
            graph.add((geom_uri, RDF.type, RSM_GEOSPARQL_ADAPTER.Geometry))
            graph.add((geom_uri, GEOSPARQL.asWKT, Literal(wkt, datatype=GEOSPARQL.wktLiteral)))
        if annotations := row.get('annotations'):
            graph.add((line_uri, RDFS.comment, Literal(annotations)))
            graph.add((geom_uri, RDFS.comment, Literal(annotations)))

    # Serialize the graph to a Turtle file

    print(f'Raw ttl file is about to be saved to {base_path}')
    output_file_path = os.path.join(base_path, f'{short_name}_raw.ttl')
    graph.serialize(destination=output_file_path, format='turtle')
