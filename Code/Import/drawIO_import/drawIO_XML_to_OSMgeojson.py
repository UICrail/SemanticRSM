# Convert drawIO XML file into OSM-style GeoJSON file.
# Note: in GeoJSON, the standard order of coordinates is (longitude, latitude) or (easting, northing)
import os
from pprint import pprint

import geojson
import xmltodict

from Import.drawIO_import.drawio_parameters import DRAWIO_XML_EXTENSION, classify_artefact_by_style
from Import.drawIO_import.geojson_helpers import create_geojson_linestring

# to transform cartesian coords on the canvas to geographic ones, we use an arbitrary transformation.
# Canvas scale: one pixel = one meter
# Remember that Y axis on the drawIO canvas is oriented down:
# Center of ETRS89-LCC Europe area (EPSG:3034) is somewhere in the Norwegian sea; for reference see epsg.io
# From OpenStreetMap
OSM_RAILWAY_TAG = {'railway': 'rail'}  # used in OpenStreetMap for annotating, well, railway-related stuff

OSM_GEOJSON_EXTENSION = '.osm.geojson'  # output file extension
TEST_DATA_FOLDER = os.path.join(os.path.curdir, 'TestData')
TEST_OUTPUTS_FOLDER = os.path.join(os.path.curdir, 'TestOutputs')


class OSMgeojsonGenerator:

    def __init__(self):
        self._input_file_extension = DRAWIO_XML_EXTENSION
        self._output_folder = None
        self.node_index = {}  # key= autoincrement node ID, value=(lat,lon)
        self.way_index = {}  # key=way (edge) id, value={'source'=<node ID>, 'target'=<node ID>, 'waypoint'= (<node ID, ...>)}
        self.label_index = {}  # key=way (edge) id, value=label string (value of connectable in the XML file)
        self.target = ''
        self.osm_doc = None
        self._define_target()

    def _define_target(self):
        self.target = "OSM GeoJSON format, with geometries"
        self.out_file_extension = OSM_GEOJSON_EXTENSION
        self.osm_doc = []

    def convert_drawio_to_osm(self, input_file_path: str, output_folder: str = TEST_OUTPUTS_FOLDER):
        """
        Main routine, to be called after instantiation.
        :param input_file_path: full path with extension (expected: .drawio.xml)
        :param output_folder:
        """
        print(f"\nTransforming a draw.io schematic track layout into {self.target}.")
        network_data = None
        if input_file_path:
            print(f"Processing File: {input_file_path}")
            network_data = self.import_xml_as_dict(input_file_path)

        if network_data:
            print("\nData dictionary derived from drawio.xml file:\n")
            (pprint(network_data, width=80))
            self._output_folder = output_folder
            self.process_dict(network_data, input_file_path)
        else:
            print("No network data found. Exiting.")

    def process_dict(self, data: dict, input_file_path):
        self.parse_dict(data)
        input_file_name = os.path.basename(input_file_path)
        output_file_name = input_file_name.replace(DRAWIO_XML_EXTENSION, self.out_file_extension)
        output_file_path = os.path.join(self._output_folder, output_file_name)

        self.save_to_file(output_file_path)
        print(f"OSM file saved to {output_file_path}")

    def parse_dict(self, data: dict):
        elements = data['mxfile']['diagram']['mxGraphModel']['root']['mxCell']
        for element in elements:
            if element.get('@edge'):
                artefact_category = classify_artefact_by_style(element['@style'])
                if artefact_category == 'slip switch':
                    print(f"INFO: edge {element['@id']} is not a linear element, but denotes a {artefact_category}")
                    self.process_edge(element, 'slip switch')
                else:
                    self.process_edge(element)
            elif element.get('@connectable'):
                self.process_connectable(element)

    def process_edge(self, item, annotation: str = ''):
        source_coords, target_coords = self.extract_coordinates(item)
        waypoints = self.extract_waypoints(item)
        source_node_id = self.get_or_create_node_id(source_coords)
        target_node_id = self.get_or_create_node_id(target_coords)
        waypoint_node_ids = ()
        if waypoints:
            for waypoint in waypoints:
                waypoint_node_id = self.get_or_create_node_id(waypoint)
                waypoint_node_ids += (waypoint_node_id,)

        self.way_index[item['@id']] = {'source': source_node_id, 'target': target_node_id,
                                       'waypoints': waypoint_node_ids, 'annotation': annotation}

        # in certain cases, the label is attached directly to the edge
        if label := item.get('@value'):
            self.label_index[item['@id']] = label

    def process_connectable(self, item):
        if (related_way := item.get('@parent')) in self.way_index.keys():
            if related_way not in self.label_index.keys():
                self.label_index[item['@parent']] = item.get('@value')
            else:
                print(f"WARNING: way {related_way} has two labels")

    def add_ways_from_index(self):
        """
        Also handles waypoints
        """
        for way_id, node_ids in self.way_index.items():
            source_coords = self.node_index[node_ids['source']]
            target_coords = self.node_index[node_ids['target']]
            waypoints = ()
            if waypoint_id_list := node_ids.get('waypoints'):
                waypoints = tuple(self.node_index[waypoint_id] for waypoint_id in waypoint_id_list)

            linestring = create_geojson_linestring(source_coords, target_coords, *waypoints)
            cleaned_label = self.cleanup_label(self.label_index.get(way_id, ''))
            tags = {'label': cleaned_label, **OSM_RAILWAY_TAG}  # empty string as default label
            if annotations := self.way_index[way_id].get('annotation'):
                tags['annotations'] = annotations
            self.osm_doc.append(geojson.Feature(type="Feature", geometry=linestring, properties=tags))

    def generate_nodes_and_ways_from_index(self):
        self.add_ways_from_index()
        feature_collection = geojson.FeatureCollection(self.osm_doc)
        osm_geojson = geojson.dumps(feature_collection, indent=2)
        return osm_geojson

    def get_or_create_node_id(self, coords) -> int:
        if coords not in self.node_index.values():
            node_id = len(self.node_index) + 1
            self.node_index[node_id] = coords
            return node_id
        else:
            return self.find_key(coords)

    def find_key(self, value):
        for key, val in self.node_index.items():
            if val == value:
                return key

    def save_to_file(self, out_path: str, new_extension: str = OSM_GEOJSON_EXTENSION):
        osm_geojson = self.generate_nodes_and_ways_from_index()
        out_path = out_path.replace(DRAWIO_XML_EXTENSION, new_extension)
        print(
            f"\nTransforming a draw.io schematic track layout into {self.target}.\nOutput file: {out_path}"
        )
        with open(out_path, 'w') as f:
            f.write(osm_geojson)

    @staticmethod
    def extract_coordinates(item):
        source_point, target_point = None, None
        for dic in item['mxGeometry']['mxPoint']:
            if dic.get('@as') == 'sourcePoint':
                source_point = dic['@x'], dic['@y']
            elif dic.get('@as') == 'targetPoint':
                target_point = dic['@x'], dic['@y']
        if source_point and target_point:
            return source_point, target_point

    @staticmethod
    def extract_waypoints(item):
        waypoints = None
        if array := item['mxGeometry'].get('Array'):
            if array.get('@as') == 'points' and len(array.get('mxPoint')) > 0:
                waypoints = tuple((waypoint['@x'], waypoint['@y']) for waypoint in array['mxPoint'])
            return waypoints

    @staticmethod
    def cleanup_label(label: str) -> str:
        TO_REMOVE = ['<br>', '<div>', '</div>']  # these are sometimes found in draw.io output
        cleaned_label = label.strip()
        for item in TO_REMOVE:
            cleaned_label = cleaned_label.replace(item, '')
        return cleaned_label

    @staticmethod
    def import_xml_as_dict(path: str) -> dict | bool:
        """returns False if not successful"""
        try:
            with open(path, 'r') as file:
                return xmltodict.parse(file.read())
        except Exception as e:
            print(e)
            return False


if __name__ == '__main__':
    from Code.Graph_transformation.full_transformation import transform_osm_to_rsm


    def test_full_transformation():
        """Transforming a station track plan in drawio xml into a sRSM topology"""
        drawio_input_file = os.path.join(TEST_DATA_FOLDER, '241023-Simple_Example+RTC-121.drawio.xml')
        generator1 = OSMgeojsonGenerator()
        generator1.convert_drawio_to_osm(drawio_input_file)
        osm_input_file = os.path.join(TEST_OUTPUTS_FOLDER, '241023-Simple_Example+RTC-121.osm.geojson')
        transform_osm_to_rsm(osm_input_file, 'New test after deep refactoring')


    def test_waypoints():
        """Testing the usage of waypoints, in drawIO, on connectors (so they are shaped as polyline)"""
        drawio_input_file = os.path.join(TEST_DATA_FOLDER, '241104 siding.drawio.xml')
        generator1 = OSMgeojsonGenerator()
        generator1.convert_drawio_to_osm(drawio_input_file)


    test_full_transformation()
    # test_waypoints()
