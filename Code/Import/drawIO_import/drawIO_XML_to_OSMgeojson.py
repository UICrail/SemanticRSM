# Convert drawIO XML file into OSM-style GeoJSON file.
# Note: in GeoJSON, the standard order of coordinates is (longitude, latitude) or (easting, northing)
import os

import geojson
from pyproj import Transformer

from Code.Import.drawIO_import.drawIO_XML_to_OSMjson import *

# to transform cartesian coords on the canvas to geographic ones, we use an arbitrary transformation.
# Canvas scale: one pixel = one meter
# Remember that Y axis on the drawIO canvas is oriented down:
CANVAS_ORIENTATION = -1
# Center of ETRS89-LCC Europe area (EPSG:3034) is somewhere in the Norwegian sea; for reference see epsg.io
CENTER_COORDS = 4115023.91, 3536037.64
# From OpenStreetMap
RAILWAY_TAG = {'railway': 'rail'}  # used in OpenStreetMap for annotating, well, railway-related stuff

OSM_GEOJSON_EXTENSION = '.osm.geojson'  # output file extension

# initialize coordinate transformer from ETRS89 to WGS84
transformer = Transformer.from_crs("EPSG:3034", "EPSG:4326")


class OSMgeojsonGenerator(OSMGenerator):

    def __init__(self):
        super().__init__()

    def _define_target(self):
        self.target = "OSM GeoJSON format, with geometries"
        self.out_file_extension = OSM_GEOJSON_EXTENSION
        self.osm_doc = []

    def add_nodes_from_index(self):
        # needed, for polymorphism
        pass

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
            tags = {'label': cleaned_label, **RAILWAY_TAG}  # empty string as default label
            if annotations := self.way_index[way_id].get('annotation'):
                tags['annotations'] = annotations
            self.osm_doc.append(geojson.Feature(type="Feature", geometry=linestring, properties=tags))

    def generate_osm_string(self) -> str:
        super().generate_osm_string()
        feature_collection = geojson.FeatureCollection(self.osm_doc)
        osm_json = geojson.dumps(feature_collection, indent=2)
        return osm_json

    def save_to_file(self, in_path: str, new_extension: str = OSM_GEOJSON_EXTENSION):
        super().save_to_file(in_path, new_extension)


def create_geojson_linestring(source, target, *waypoints):
    lon_lat_array = ()
    if waypoints:
        lon_lat_array = cartesian_to_lonlat(*waypoints)
    way_coords = (
        cartesian_to_lonlat(source),
        *lon_lat_array,
        cartesian_to_lonlat(target)
    )
    return geojson.LineString(way_coords)


def create_geojson_point(lon: float | str, lat: float | str):
    # TODO: move this helper function to some helper module
    return geojson.Point(cartesian_to_lonlat((float(lon), float(lat))))


def cartesian_to_lonlat(*coords: tuple[str | float, str | float]):
    # TODO: move this helper function to some helper module
    result = []
    for coord in coords:
        result.append(transformer.transform(CANVAS_ORIENTATION * float(coord[1]) + CENTER_COORDS[1],
                                            float(coord[0]) + CENTER_COORDS[0]))
    return tuple(result)


if __name__ == '__main__':
    from Code.Graph_transformation.full_transformation import transform_osm_to_rsm


    def test1():
        test_file = os.path.abspath(os.path.join(os.path.curdir, 'TestData', '241023-Simple_Example+RTC-121'))
        generator1 = OSMgeojsonGenerator()
        generator1.convert_drawio_to_osm(test_file)
        test_file = test_file + OSM_GEOJSON_EXTENSION
        transform_osm_to_rsm(test_file, 'Pierre_Tane_test_121')


    # Testing the usage of waypoints, in drawIO, on connectors (so they are shaped as polyline)
    def test_waypoints():
        test_file = os.path.join(os.path.curdir, 'TestData/241104 siding.drawio.xml')
        generator1 = OSMgeojsonGenerator()
        generator1.convert_drawio_to_osm(test_file)


    test_waypoints()
