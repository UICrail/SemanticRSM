"""
Purpose: pick an OSM geojson file and transform it into an RSM-compliant topology graph
"""
from Code.Export.export_to_kml import ttl_to_kml
from Code.Graph_transformation.chain_linear_elements import chain_linear_elements
from Code.Import.OSM_import import osm_import
from Code.Graph_transformation.split_linear_elements import split_linear_elements


def transform_osm_to_rsm(osm_geojson_file):
    print("reading the OSM file: ", osm_geojson_file)
    # Read the OSM geojson file
    osm_import.osm_import(osm_geojson_file)
    # Split the linear elements if needed
    split_linear_elements("/Users/airymagnien/PycharmProjects/SemanticRSM/Intermediate_files/osm_railways_raw.ttl")
    chain_linear_elements("/Users/airymagnien/PycharmProjects/SemanticRSM/Intermediate_files/osm_railways_split.ttl",
                          "/Users/airymagnien/PycharmProjects/SemanticRSM/Intermediate_files/osm_railways_chained.ttl")
    ttl_to_kml("/Users/airymagnien/PycharmProjects/SemanticRSM/Intermediate_files/osm_railways_chained.ttl",
               "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/osm_railways_chained.kml")


if __name__ == "__main__":
    transform_osm_to_rsm("/Users/airymagnien/PycharmProjects/SemanticRSM/Source_data/OSM/Sankt_Pölten.geojson")
