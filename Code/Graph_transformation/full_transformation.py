"""
Purpose: pick an OSM geojson file and transform it into an RSM-compliant topology.ttl graph
"""
import os
from Code.Export.export_wkt_to_kml import ttl_to_kml
from Code.Graph_transformation.step02_join_linear_elements import join_linear_elements
from Code.Import.OSM_import.osm_geojson_to_ttl import osm_import
from Code.Graph_transformation.step01_split_linear_elements import split_linestrings_in_file
from Graph_transformation.step03_add_ports import add_ports_to_linear_elements
from Graph_transformation.step04_add_port_properties import set_port_connections, set_navigabilities
from Graph_transformation.step04b_add_slip_functionality import add_slip_functionality

BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "Output_files", "Intermediate_files")


def generate_file_path(short_name, stage):
    return os.path.join(BASE_PATH, f"osm_{short_name}_{stage}.ttl")




def transform_osm_to_rsm(osm_geojson_path, short_name):
    """

    :param osm_geojson_path: source data
    :param short_name: will be used in the name of generated files
    :return: None
    """
    print(f"Reading the OSM file: {osm_geojson_path}")

    # Read the OSM geojson file
    osm_import(osm_geojson_path, short_name)

    # Split the linear elements if needed
    split_linestrings_in_file(generate_file_path(short_name, "raw"), short_name)

    join_linear_elements(
        generate_file_path(short_name, "split"),
        generate_file_path(short_name, "joint")
    )

    add_ports_to_linear_elements(
        generate_file_path(short_name, "joint"),
        generate_file_path(short_name, "with_ports")
    )

    set_port_connections(
        generate_file_path(short_name, "with_ports"),
        generate_file_path(short_name, "with_connected_ports")
    )

    set_navigabilities(
        generate_file_path(short_name, "with_connected_ports"),
        generate_file_path(short_name, "with_navigabilities"),
        double_slip_crossings=True
    )

    add_slip_functionality(
        generate_file_path(short_name, "with_navigabilities"),
        generate_file_path(short_name, "with_slip_functionality")
    )

    ttl_to_kml(
        generate_file_path(short_name, "with_ports"),
        os.path.join(BASE_PATH, f"osm_{short_name}.kml")
    )


def osm_via_rsm_to_kml(osm_geojson_file, short_name):
    """
    Direct transformation, without attempting to split or merge.
    """
    print(f"Reading the OSM file: {osm_geojson_file}")
    osm_import(osm_geojson_file)
    ttl_to_kml(
        generate_file_path(short_name, "raw"),
        os.path.join(BASE_PATH, f"osm_{short_name}_direct.kml")
    )


if __name__ == "__main__":
    transform_osm_to_rsm(
        os.path.join(os.path.dirname(__file__), "..", "..", "Source_data", "OSM", "Ventimiglia_Albenga.geojson"),
        "Ventimiglia-Albenga")
