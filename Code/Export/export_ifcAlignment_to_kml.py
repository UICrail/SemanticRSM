import numpy as np
import simplekml
from pyproj import Transformer
from rdflib import Graph
from rdflib.namespace import RDF
from shapely.wkt import loads

from Code.Import.SD1_import.cdm_namespaces import *
from Graph_transformation.step03_add_ports import wgs84_geod
from Import.SD1_import.helper_functions import arc_end_coords


def alignment_to_kml(source_file_path: str, output_file: str, source_epsg: int = 4326) -> None:
    # code to export ifc alignment to kml
    segments = parse_ttl_for_horizontal_segments(source_file_path)
    output = linestrings_to_kml(generate_wkt(segments), Transformer.from_crs(source_epsg, 4326, always_xy=True))
    output.save(output_file)
    print(f"KML file was successfully generated: {output_file}")


def parse_ttl_for_horizontal_segments(source_file_path: str, arcs_only: bool = False) -> dict:
    segment_dict = {}  # segments and their params
    g = Graph()
    g.parse(source_file_path, format="turtle")
    for horizontal_alignment in g.subjects(predicate=RDF.type, object=IFC_NAMESPACE.IfcAlignmentHorizontal):
        for segment_nest in g.objects(subject=horizontal_alignment,
                                      predicate=IFC_NAMESPACE.isNestedBy_IfcObjectDefinition):
            for segment in g.objects(subject=segment_nest, predicate=IFC_NAMESPACE.relatedObjects_IfcRelNests):
                segment_params = next(
                    g.objects(subject=segment, predicate=IFC_NAMESPACE.designParameters_IfcAlignmentSegment))
                start_coords = str(next(g.objects(subject=segment_params,
                                                  predicate=IFC_NAMESPACE.startPoint_IfcAlignmentHorizontalSegment))).strip(
                    '[').strip(']').split()
                start_coords = [float(x) for x in start_coords]
                try:
                    start_direction = float(next(g.objects(subject=segment_params,
                                                           predicate=IFC_NAMESPACE.startDirection_IfcAlignmentHorizontalSegment)))
                except StopIteration:
                    start_direction = None
                try:
                    start_r = float(next(g.objects(subject=segment_params,
                                                   predicate=IFC_NAMESPACE.startRadiusOfCurvature_IfcAlignmentHorizontalSegment)))
                except StopIteration:
                    start_r = None
                try:
                    length = float(next(g.objects(subject=segment_params,
                                                  predicate=IFC_NAMESPACE.segmentLength_IfcAlignmentHorizontalSegment)))
                except StopIteration:
                    length = None
                try:
                    shape = str(next(g.objects(subject=segment_params,
                                               predicate=IFC_NAMESPACE.predefinedType_IfcActionRequest))).split('#')[1]
                except StopIteration:
                    shape = None
                if not arcs_only or (arcs_only and start_r != 0):
                    segment_dict[segment] = Segment(start_coords, start_direction, start_r, length, shape)
    return segment_dict


class Segment:
    def __init__(self, start_coords: list[float], start_direction: float, radius: float, length: float, shape: str):
        self.start_coords = np.array(start_coords)
        self.shape = shape
        self.length = length
        self.radius = radius
        self.start_direction = start_direction
        # self.end_direction = end_direction
        self.to_wkt()

    def to_wkt(self):
        result = None
        if self.length > 0:
            end_coords = arc_end_coords(self.start_coords, self.start_direction, self.length, self.radius)
            if self.shape == 'LINE':
                result = f'LINESTRING({self.start_coords[0]} {self.start_coords[1]}, {end_coords[0]} {end_coords[1]})'
            elif self.shape == 'CIRCULARARC':
                linestring_contents = ''
                increment = 1  # meter
                position = 0  # meter from start
                while position < self.length:
                    coords = arc_end_coords(self.start_coords, self.start_direction, position, self.radius)
                    linestring_contents += f'{coords[0]} {coords[1]}, '
                    position += increment
                linestring_contents += f'{end_coords[0]} {end_coords[1]}'
                result = f'LINESTRING({linestring_contents})'
            if result:
                print(result)
        return result


def generate_wkt(segment_dict) -> list[str]:
    result = []
    for segment in segment_dict.values():
        wkt = segment.to_wkt()
        if wkt:
            result.append(wkt)
    return result


def linestrings_to_kml(wkts, transformer: Transformer) -> simplekml.Kml:
    """
    Function to convert a list of WKT LineStrings into a KML object using simplekml.
    :param wkts: List of WKT (Well-Known Text) geometries.
    :param transformer: A Transformer object for converting coordinates from one CRS to (here) EPSG:4326, i.e. WGS84
    :return: A simplekml.Kml object.
    """
    # Create a KML object
    kml = simplekml.Kml()

    # Process each WKT Linestring
    for idx, linestring_wkt in enumerate(wkts):
        # Convert the WKT to a Shapely LineString
        linestring_geom = loads(linestring_wkt)

        # Extract coordinates from the LineString
        coords = [(x, y) for x, y in linestring_geom.coords]  # simplekml requires tuples of (lon, lat)
        # Convert coords to EPSG:4326
        wgs84_coords = [transformer.transform(x, y) for x, y in coords]

        # Add a LineString to the KML
        linestring = kml.newlinestring(name=f"Linestring {idx + 1}", description="Generated from WKT")
        linestring.coords = wgs84_coords  # Assign the coordinates to the LineString
        linestring.extrude = 1  # Optional (for 3D viewing)

    # Return the KML object (can later be saved or converted to a string)
    return kml
