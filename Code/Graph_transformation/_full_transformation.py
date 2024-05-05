"""
Purpose: pick an OSM geojson file and transform it into an RSM-compliant topology.ttl graph
"""
from Code.Export.export_to_kml import ttl_to_kml
from Code.Graph_transformation.chain_linear_elements import chain_linear_elements
from Code.Import.OSM_import import osm_import
from Code.Graph_transformation.split_linear_elements import split_linestrings_in_file


def transform_osm_to_rsm(osm_geojson_path, short_name):
    print("reading the OSM file: ", osm_geojson_path)
    # Read the OSM geojson file
    osm_import.osm_import(osm_geojson_path, short_name)
    # Split the linear elements if needed
    split_linestrings_in_file(
        "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{}_raw.ttl".format(
            short_name), short_name)
    chain_linear_elements(
        "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{}_split.ttl".format(
            short_name),
        "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{}_chained.ttl".format(
            short_name))
    ttl_to_kml(
        "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{}_chained.ttl".format(
            short_name),
        "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/osm_{}_chained.kml".format(short_name))


def osm_via_rsm_to_kml(osm_geojson_file, short_name):
    """
    direct transformation, without attempting to split or merge
    :param short_name:
    :param osm_geojson_file:
    :return:
    """
    print("reading the OSM file: ", osm_geojson_file)
    osm_import.osm_import(osm_geojson_file)
    ttl_to_kml("/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{}_raw.ttl".format(
        short_name),
               "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/osm_{}_direct.kml".format(short_name))


if __name__ == "__main__":
    transform_osm_to_rsm("/Users/airymagnien/PycharmProjects/SemanticRSM/Source_data/OSM/Ventimiglia_Albenga.geojson",
                         "Ventimiglia-Albenga")
    transform_osm_to_rsm("/Users/airymagnien/PycharmProjects/SemanticRSM/Source_data/OSM/Sankt_Pölten.geojson",
                         "Sankt_Pölten")
