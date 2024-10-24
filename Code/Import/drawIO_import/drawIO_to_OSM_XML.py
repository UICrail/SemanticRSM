# Convert drawIO XML file into OSM-style JSON file

import os
from lxml import etree
from pprint import pprint
import xmltodict

# Constants
OSM_VERSION = "0.6"
GENERATOR = "Python"
# noinspection HttpUrlsUsage
NAMESPACE_URI = "http://osm.org"


# drawIO XML to dict

def import_xml_as_dict(path: str) -> dict | bool:
    """returns False if not successful"""
    try:
        with open(path, 'r') as file:
            return xmltodict.parse(file.read())
    except Exception as e:
        print(e)
        return False


# From Python dict to OSM JSON file

class OSMGenerator:
    """Turns the original diagram into a JSON OSM file.
    Each straight segment becomes an OSM way. Consecutive segments will be merged under the standard OSM processing"""

    def __init__(self):
        self._input_file_extension = ".drawio.xml"
        self.node_index = {}  # key= autoincrement node ID, value=(lat,lon)
        self.way_index = {}  # key=way (edge) id, value={'source'=<node ID>, 'target'=<node ID>}
        self.label_index = {}  # key=way (edge) id, value=label string (value of connectable in the XML file)
        self.target = ''
        self.osm_doc = None
        self._define_target()

    def _define_target(self):
        self.target = "OSM native format, with nodes, ways, and possibly relations (not used)"
        self.out_file_extension = '.osm.xml'
        self.osm_doc = etree.Element("osm", version=OSM_VERSION, generator=GENERATOR, nsmap={None: NAMESPACE_URI})

    def create_osm_node(self, node_id, lat, lon, tags: dict):
        node = etree.SubElement(self.osm_doc, "node", id=str(node_id), lat=str(lat), lon=str(lon))
        if tags:
            for key, value in tags.items():
                etree.SubElement(node, "tag", k=key, v=value)

    def create_osm_way(self, way_id, node_ids, tags: dict):
        way = etree.SubElement(self.osm_doc, "way", id=str(way_id))
        for node_id in node_ids:
            etree.SubElement(way, "nd", ref=str(node_id))
        if tags:
            for k, v in tags.items():
                etree.SubElement(way, "tag", k=k, v=v)

    def add_nodes_from_index(self):
        for node_id, coords in self.node_index.items():
            self.create_osm_node(node_id, coords[0], coords[1], {})

    def parse_dict(self, data: dict):
        element_list = data['mxfile']['diagram']['mxGraphModel']['root']['mxCell']
        for item in element_list:
            if item.get('@edge'):
                self.process_edge(item)
            elif item.get('@connectable'):
                self.process_connectable(item)

    def process_edge(self, item):
        source_coords, target_coords = self.extract_coordinates(item)
        source_node_id = self.get_or_create_node_id(source_coords)
        target_node_id = self.get_or_create_node_id(target_coords)
        self.way_index[item['@id']] = {'source': source_node_id, 'target': target_node_id}

    def process_connectable(self, item):
        # TODO: expand this method to handle slip crossing characterization
        if item.get('@parent') in self.way_index.keys():
            self.label_index[item['@parent']] = item.get('@value')

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
    def cleanup_label(label: str) -> str:
        TO_REMOVE = ['<br>', '<div>', '</div>']  # these are sometimes found in draw.io output
        cleaned_label = label
        for item in TO_REMOVE:
            cleaned_label = cleaned_label.replace(item, '')
        return cleaned_label

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

    def generate_osm_string(self):
        self.add_nodes_from_index()
        self.add_ways_from_index()

    def save_to_file(self, out_path: str):
        self.generate_osm_string()
        tree = etree.ElementTree(self.osm_doc)
        tree.write(out_path + '.osm.xml', pretty_print=True, xml_declaration=True, encoding="UTF-8")

    def add_ways_from_index(self):
        for way_id, nodes in self.way_index.items():
            clean_label = self.cleanup_label(self.label_index.get(way_id, ''))
            tag = {'label': clean_label}
            self.create_osm_way(way_id, (nodes['source'], nodes['target']), tags=tag)

    def convert_drawio_to_osm(self, input_file_path: str):
        """
        Main routine
        :param input_file_path: filename without extension
        """
        print(f"\nTransforming a draw.io schematic track layout into {self.target}.")
        print(f"File: {input_file_path}.{self._input_file_extension}")
        print("\nCurrent directory: ", os.getcwd())

        network_data = import_xml_as_dict(input_file_path + self._input_file_extension)

        if network_data:
            print("\nData dictionary derived from drawio.xml file:\n")
            (pprint(network_data, width=80))
            self.parse_dict(network_data)
            self.save_to_file(input_file_path)
        else:
            print("No network data found")


if __name__ == '__main__':
    file_path = 'TestData/241023-Simple_Example+RTC-121'
    OSMGenerator().convert_drawio_to_osm(file_path)
