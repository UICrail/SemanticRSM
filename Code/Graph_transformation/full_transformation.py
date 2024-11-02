"""
Purpose: pick an OSM geojson file and transform it into an RSM-compliant topology.ttl graph
"""
import os

from Code.Export.export_wkt_to_kml import ttl_to_kml
from Code.Graph_transformation.step01_split_linear_elements import split_linestrings_in_file
from Code.Graph_transformation.step02_join_linear_elements import join_linear_elements
from Code.Import.OSM_import.osm_geojson_to_ttl import osm_to_ttl
from Graph_transformation.step03_add_ports import add_ports_to_linear_elements
from Graph_transformation.step04_add_port_properties import set_port_connections, set_navigabilities
from Graph_transformation.step04b_add_slip_functionality import add_slip_functionality

BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "Output_files", "Intermediate_files")
DOUBLE_SLIP_CROSSINGS = False
NAVIGABILITIES_SUFFIX = "with_navigabilities"
KML_SUFFIX = " including slip switch representation"


def generate_file_path(short_name, stage, base_path=BASE_PATH):
    return os.path.join(base_path, f"{short_name}_{stage}.ttl")


def transform_osm_to_rsm(osm_geojson_path, short_name, base_path=BASE_PATH) -> str:
    """
    :param osm_geojson_path: source data
    :param short_name: will be used in the name of generated files
    :return: resulting ttl file as string
    """
    print(f"Reading the OSM file: {osm_geojson_path}")

    # Read the OSM geojson file and produce the raw ttl file
    osm_to_ttl(osm_geojson_path, short_name=short_name, base_path=base_path)
    print(f'TTL file produced from the OSM geojson file, output at {base_path}')

    # Process linear elements
    result = run_process_steps(short_name, base_path)
    return result


def run_process_steps(short_name, base_path=BASE_PATH) -> str:
    """

    :param short_name:
    :param base_path:
    :return: processed ttl file as string
    """

    split_linestrings_in_file(generate_file_path(short_name, "raw", base_path), short_name)
    join_linear_elements(
        generate_file_path(short_name, "split", base_path),
        generate_file_path(short_name, "joint", base_path)
    )
    add_ports_to_linear_elements(
        generate_file_path(short_name, "joint", base_path),
        generate_file_path(short_name, "with_ports", base_path)
    )
    set_port_connections(
        generate_file_path(short_name, "with_ports", base_path),
        generate_file_path(short_name, "with_connected_ports", base_path)
    )
    set_navigabilities(
        generate_file_path(short_name, "with_connected_ports", base_path),
        generate_file_path(short_name, NAVIGABILITIES_SUFFIX, base_path),
        double_slip_crossings=DOUBLE_SLIP_CROSSINGS
    )
    result = add_slip_functionality(
        generate_file_path(short_name, NAVIGABILITIES_SUFFIX, base_path),
        generate_file_path(short_name, "with_slip_functionality", base_path)
    )
    ttl_to_kml(
        generate_file_path(short_name, NAVIGABILITIES_SUFFIX, base_path),
        os.path.join(BASE_PATH, f"{short_name}{KML_SUFFIX}.kml")
    )
    return result


def osm_via_rsm_to_kml(osm_geojson_file, short_name, base_path=BASE_PATH):
    """
    Direct transformation, without attempting to split or merge.
    """
    print(f"Reading the OSM file: {osm_geojson_file}")
    osm_to_ttl(osm_geojson_file)
    ttl_to_kml(
        generate_file_path(short_name, "raw"),
        os.path.join(base_path, f"osm_{short_name}_direct.kml")
    )


if __name__ == "__main__":
    transform_osm_to_rsm(
        os.path.join(os.path.dirname(__file__), "..", "..", "Source_data", "OSM", "Ventimiglia_Albenga.geojson"),
        "Ventimiglia-Albenga")
