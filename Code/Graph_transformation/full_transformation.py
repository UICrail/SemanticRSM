# See readme.md for explanations
import os

from Code.Export.export_ttl_to_kml import ttl_to_kml
from Code.Graph_transformation.step01_split_linear_elements import split_linestrings_in_file
from Code.Graph_transformation.step02_join_linear_elements import join_linear_elements
from Graph_transformation.step03_add_ports import add_ports_to_linear_elements
from Graph_transformation.step04_add_port_properties import set_port_connections, set_navigabilities
from Graph_transformation.step04b_add_slip_functionality import add_slip_functionality

OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'TestOutput')
NAVIGABILITIES_SUFFIX = "with_navigabilities"
KML_SUFFIX = " including slip switch representation"


def generate_file_path(short_name, stage, to_folder=OUTPUT_FOLDER):
    return os.path.join(to_folder, f"{short_name}_{stage}.ttl")


def transform_geojson_to_rsm(geojson_path, short_name, output_folder=OUTPUT_FOLDER, all_double_slip: bool = False) -> str:
    """

    :param geojson_path: source data (if from OSM, should be pre-processed)
    :param short_name: will be used in the name of generated files
    :param output_folder: folder for the ttl file
    :param all_double_slip: if True, all crossings will default to double slip
    :return: resulting ttl file as string
    """
    print()
    print("Preparing the transformation of an OSM file (GeoJSON format) into a sRSM file (TTL format)")
    print(f"Reading the OSM file: {geojson_path}")

    # Read the OSM geojson file and produce the raw ttl file
    from Import.OSM_import.osm_geojson_to_ttl import geojson_to_ttl
    geojson_to_ttl(geojson_path, short_name=short_name, base_path=output_folder)
    print(f'TTL file produced from the OSM geojson file, output at {output_folder}')

    # Process linear elements
    result = run_process_steps(short_name, output_folder, all_double_slip)
    return result


def run_process_steps(short_name, output_folder=OUTPUT_FOLDER, all_double_slip: bool = False) -> str:
    """

    :param all_double_slip:
    :param short_name:
    :param output_folder:
    :return: processed ttl file as string
    """

    split_linestrings_in_file(generate_file_path(short_name, "raw", output_folder), short_name)
    join_linear_elements(
        generate_file_path(short_name, "split", output_folder),
        generate_file_path(short_name, "joint", output_folder)
    )
    add_ports_to_linear_elements(
        generate_file_path(short_name, "joint", output_folder),
        generate_file_path(short_name, "with_ports", output_folder)
    )
    set_port_connections(
        generate_file_path(short_name, "with_ports", output_folder),
        generate_file_path(short_name, "with_connected_ports", output_folder)
    )
    set_navigabilities(
        generate_file_path(short_name, "with_connected_ports", output_folder),
        generate_file_path(short_name, NAVIGABILITIES_SUFFIX, output_folder),
        double_slip_crossings=all_double_slip
    )
    result = add_slip_functionality(
        generate_file_path(short_name, NAVIGABILITIES_SUFFIX, output_folder),
        generate_file_path(short_name, "with_slip_functionality", output_folder)
    )
    ttl_to_kml(
        generate_file_path(short_name, NAVIGABILITIES_SUFFIX, output_folder),
        os.path.join(OUTPUT_FOLDER, f"{short_name}{KML_SUFFIX}.kml")
    )
    return result


def osm_via_rsm_to_kml(osm_geojson_file, short_name, base_path=OUTPUT_FOLDER):
    """
    Direct transformation, without attempting to split or merge.
    """
    print(f"Reading the OSM file: {osm_geojson_file}")
    from Import.OSM_import.osm_geojson_to_ttl import geojson_to_ttl
    geojson_to_ttl(osm_geojson_file)
    ttl_to_kml(
        generate_file_path(short_name, "raw"),
        os.path.join(base_path, f"osm_{short_name}_direct.kml")
    )


if __name__ == "__main__":
    # transform_geojson_to_rsm(
    #     os.path.join(os.path.dirname(__file__), "..", "..", "Source_data", "OSM", "Ventimiglia_Albenga.geojson"),
    #     "Ventimiglia-Albenga")
    source_path = '/Users/airymagnien/PycharmProjects/SemanticRSM/Code/Graph_transformation/TestData/Sankt Pölten area_preprocessed.geojson'
    transform_geojson_to_rsm(source_path, 'SPO_preprocessed', all_double_slip=True)

