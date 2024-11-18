# Imports GeoJSON file using GeoPandas
# WARNING: does not seem to work properly with GeoJSON export from OSM using the Overpass API;
# overlapping linestrings would cause trouble in the subsequent processing.
import datetime
import json
import os.path

import geopandas as gpd
import rdflib
from rdflib import RDF, Literal, RDFS, OWL, DC
from shapely.geometry import LineString, Point

from Code.Namespaces import *
from Graph_transformation.full_transformation import OUTPUT_FOLDER

PREPROCESSED = 'preprocessed_for_sRSM_conversion'


def initialize_rdf_graph():
    g = rdflib.Graph()
    g.bind("geo", GEOSPARQL)
    g.bind("rsm", RSM_TOPOLOGY)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("rsm", RSM_GEOSPARQL_ADAPTER)
    g.bind("", WORK)
    return g


def preprocess_osm_geojson(osm_file_path: str, short_name: str = "", base_path: str = OUTPUT_FOLDER) -> str:
    """
    Processes an OpenStreetMap (OSM) GeoJSON file by updating railway classification and adding metadata, and
    then saves the result to a specified directory.

    The function reads the provided GeoJSON file into a GeoDataFrame, modifies it to classify 'rail'
    railway attributes as 'LinearElement', adds metadata about the preprocessing time, and saves it to
    a new GeoJSON file.

    :param osm_file_path: Full file path to the input OSM GeoJSON file
    :param short_name: Optional short name to be included in the output file name for better identification
    :param base_path: Directory path where the processed GeoJSON file will be saved
    :return: The full path to the preprocessed GeoJSON output file
    """

    gdf = gpd.read_file(osm_file_path)
    gdf.loc[gdf['railway'] == 'rail', 'rsm_class'] = 'LinearElement'

    # add metadata
    # Convert GeoDataFrame to GeoJSON format
    geojson_dict = gdf.to_json()
    geojson_dict = json.loads(geojson_dict)
    geojson_dict[PREPROCESSED] = f"{datetime.datetime.now()}"

    # Set output file path
    output_file_path = os.path.join(base_path, f'{short_name}_preprocessed.geojson')

    # Save the modified GeoDataFrame back to a GeoJSON file
    with open(output_file_path, 'w') as f:
        json.dump(geojson_dict, f)
    print(f'Preprocessed GeoJSON file is about to be saved to {base_path}')
    return output_file_path


def process_geometry(row):
    if isinstance(row.geometry, (LineString, Point)):
        return row.geometry.wkt
    return str(row.geometry)


def osm_to_ttl(osm_file_path: str, short_name: str = "", base_path: str = OUTPUT_FOLDER,
               linear_element_prefix: str = 'linear_element',
               geometry_prefix: str = 'geom', with_geometry: bool = True):
    """
    Converts an OpenStreetMap (OSM) file to Turtle (TTL) format for RDF representation.
    First, checks whether the input file has a PREPROCESSED key in its GeoJSON metadata.
    If so, geojson_to_ttl is called with the appropriate parameters.
    If not, preprocess_osm_geojson is called and the output file is placed into the base_path folder, then
    geojson_to_ttl is called with this pre-processed file path as geojson_file_path argument.

    :param osm_file_path: Path to the OSM file to be converted
    :param short_name: Optional short name for the output file, defaults to an empty string
    :param base_path: Base directory path to save the TTL file, defaults to OUTPUT_FOLDER
    :param linear_element_prefix: Prefix for linear elements in the TTL file,
                                  defaults to 'linear_element'
    :param geometry_prefix: Prefix for geometry elements in the TTL file, defaults to 'geom'
    :param with_geometry: Flag to indicate whether to include geometry information in
                          the TTL file, defaults to True
    :return: None
    """

    # Read the OSM file into a GeoDataFrame
    gdf = gpd.read_file(osm_file_path)

    # Convert GeoDataFrame to GeoJSON format
    geojson_dict = gdf.to_json()
    geojson_dict = json.loads(geojson_dict)

    # Check if the input OSM file has a "PREPROCESSED" key in its metadata
    if PREPROCESSED in geojson_dict:
        # Call geojson_to_ttl with the input file
        geojson_to_ttl(
            geojson_file_path=osm_file_path,
            short_name=short_name,
            base_path=base_path,
            linear_element_prefix=linear_element_prefix,
            geometry_prefix=geometry_prefix,
            with_geometry=with_geometry
        )
    else:
        # Preprocess the OSM GeoJSON file and save it to the base directory
        preprocessed_file_path = preprocess_osm_geojson(
            osm_file_path=osm_file_path,
            short_name=short_name,
            base_path=base_path
        )
        # Call geojson_to_ttl with the preprocessed file
        geojson_to_ttl(
            geojson_file_path=preprocessed_file_path,
            short_name=short_name,
            base_path=base_path,
            linear_element_prefix=linear_element_prefix,
            geometry_prefix=geometry_prefix,
            with_geometry=with_geometry
        )


def geojson_to_ttl(geojson_file_path: str, short_name: str = "", base_path: str = OUTPUT_FOLDER,
                   linear_element_prefix: str = 'linear_element', geometry_prefix: str = 'geom',
                   with_geometry: bool = True):
    """
    Takes the GeoJSON file (OpenStreetMap-style) and turns it into a ttl file. RSM compliance will however be achieved
    in subsequent transformations (see Graph_transformation folder).
    :param base_path:
    :param geometry_prefix:
    :param linear_element_prefix: used to build URIRefs
    :param geojson_file_path:
    :param short_name: will be used for the intermediate and final file naming
    :param with_geometry: if False, geometries will not be associated with the linear elements via hasNominalGeometry.
    In such case, only the URIs will tell which linear element matches which geometry.
    :return: None (a file is created)
    """
    from rdflib import URIRef

    # Initialize RDF graph
    graph = initialize_rdf_graph()

    # Load OSM data (assumed to be in GeoJSON format) with GeoPandas
    gdf = gpd.read_file(geojson_file_path)

    # Assuming the 'railway' attribute is within the properties field, filter for railway lines
    railways = gdf[gdf['railway'] == 'rail']  # tagged value 'rail' designates a track

    # Add ontology name and other annotations
    graph.add((WORK[''], RDF.type, OWL.Ontology))
    graph.add((WORK[''], RDFS.label, Literal(short_name, lang='en')))
    graph.add((WORK[''], DC.creator, Literal("sRSM Flask App")))

    # Process elements
    for index, row in railways.iterrows():
        if rsm_class := row.get('rsm_class'):
            if rsm_class == 'LinearElement':
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
            elif rsm_class == 'SpotLocation':
                spot_uri = WORK[f"spot_location_{index}"]
                geom_uri = WORK[f"spot_{index}"]
                asso_uri = WORK[f"location_on_net_element_{index}"]
                wkt = process_geometry(row)
                # TODO: replace object by proper URIRef
                graph.add((spot_uri, RDF.type, URIRef('http://cdm.ovh/rsm/location#SpotLocation')))
                graph.add((geom_uri, RDF.type, RSM_GEOSPARQL_ADAPTER.Geometry))
                graph.add((geom_uri, GEOSPARQL.asWKT, Literal(wkt, datatype=GEOSPARQL.wktLiteral)))
                graph.add((spot_uri, RSM_GEOSPARQL_ADAPTER.hasNominalGeometry, geom_uri))
                graph.add((asso_uri, RDF.type, URIRef('http://cdm.ovh/rsm/location#LocationOnNetElement')))
                graph.add((spot_uri, URIRef('http://cdm.ovh/rsm/location#associatedNetElement'), asso_uri))
                graph.add((asso_uri, URIRef('http://cdm.ovh/rsm/location#bound'), Literal(0.123)))
                graph.add((asso_uri, RSM_TOPOLOGY.onElement, OWL.Nothing))

    # Serialize the graph to a Turtle file

    print(f'Raw ttl file is about to be saved to {base_path}')
    output_file_path = os.path.join(base_path, f'{short_name}_raw.ttl')
    graph.serialize(destination=output_file_path, format='turtle')


if __name__ == '__main__':
    def test_osm_to_ttl_transformation():
        osm_to_ttl(osm_file_path='./TestData/Sankt_Pölten.geojson', short_name='Sankt Pölten area',
                   base_path='./TestOutput', linear_element_prefix='linear_element', geometry_prefix='geom',
                   with_geometry=True)


    def test_preprocess():
        preprocess_osm_geojson(osm_file_path='./TestData/Sankt_Pölten.geojson', short_name='Sankt Pölten area',
                               base_path='./TestOutput')

    # test_preprocess()
    test_osm_to_ttl_transformation()  # success on 202411171428
    pass
