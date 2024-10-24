# Convert drawIO XML file into OSM-style GeoJSON file.
import geojson
from drawIO_to_OSM_XML import *
from pyproj import Transformer

# to transform cartesian coords on the canvas to geographic ones, we use an arbitrary transformation.
# Canvas units = one meter
# Remember that Y axis on the canvas is oriented down
# NTF Lambert zone 1 to WGS84:
transformer = Transformer.from_crs("EPSG:27571", "EPSG:4326")
CENTER_COORDS = 603357.78, 835717.15  # of NTF Lambert zone 1

# From OpenStreetMap
RAILWAY_TAG = {'railway': 'rail'}  # used in OpenStreetMap for annotating, well, railway-related stuff


def _cartesian_to_lonlat(coords: tuple[str, str], permute=False) -> tuple[str, str]:
    result = transformer.transform(float(coords[0]) + CENTER_COORDS[0], -float(coords[1]) + CENTER_COORDS[1])
    if permute:
        return result[1], result[0]
    return result[0], result[1]


class OSMjsonGenerator(OSMGenerator):

    def __init__(self):
        super().__init__()

    def _define_target(self):
        self.target = "OSM GeoJSON format, with geometries"
        self.out_file_extension = '.osm.geojson'
        self.osm_doc = []

    @staticmethod
    def _create_geojson_point(lon, lat):
        return geojson.Point(_cartesian_to_lonlat((float(lon), float(lat))))

    @staticmethod
    def _create_geojson_linestring(source, target):
        way_coords = (
            _cartesian_to_lonlat(source),
            _cartesian_to_lonlat(target)
        )
        return geojson.LineString(way_coords)

    def add_nodes_from_index(self):
        # needed, for polymorphism
        pass

    def add_ways_from_index(self):
        """overrides the method in super()"""
        for way_id, node_ids in self.way_index.items():
            source_coords = self.node_index[node_ids['source']]
            target_coords = self.node_index[node_ids['target']]

            linestring = self._create_geojson_linestring(source_coords, target_coords)
            cleaned_label = self.cleanup_label(self.label_index.get(way_id, ''))
            tags = {'label': cleaned_label, **RAILWAY_TAG}  # empty string as default label
            self.osm_doc.append(geojson.Feature(type="Feature", geometry=linestring, properties=tags))

    def generate_osm_string(self):
        super().generate_osm_string()
        feature_collection = geojson.FeatureCollection(self.osm_doc)
        osm_json = geojson.dumps(feature_collection, indent=2)
        return osm_json

    def save_to_file(self, out_path: str):
        osm_json = self.generate_osm_string()
        with open(out_path + '.osm.geojson', 'w') as f:
            f.write(osm_json)


if __name__ == '__main__':
    from Code.Import.OSM_import.osm_geojson_to_ttl import osm_import
    from Code.Graph_transformation.full_transformation import transform_osm_to_rsm

    file_path = 'TestData/241023-Simple_Example+RTC-121'
    OSMjsonGenerator().convert_drawio_to_osm(file_path)
    osm_import(file_path + '.osm.geojson', "Pierre's test, 121")
    transform_osm_to_rsm(file_path + '.osm.geojson', "Pierre's test, 121")
