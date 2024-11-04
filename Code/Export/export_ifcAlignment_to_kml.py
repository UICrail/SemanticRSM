import numpy as np
from fastkml import kml
from rdflib import Graph
from rdflib.namespace import RDF
from shapely.wkt import loads

from Code.Import.SD1_import.cdm_namespaces import *
from Import.SD1_import.helper_functions import arc_end_coords


def alignment_to_kml(source_file_path: str, output_file: str) -> None:
    # code to export ifc alignment to kml
    segments = parse_ttl_for_horizontal_segments(source_file_path)


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


def linestrings_to_kml(wkts) -> str:
    # Create a new KML object
    k = kml.KML()

    # Create a new document for the KML object
    document = kml.Document()
    k.append(document)

    # Go through each of the WKT LineStrings
    for linestring_wkt in wkts:
        # Convert the WKT to a shapely geometry (LineString)
        linestring_geometry = loads(linestring_wkt)

        # Create a new KML place mark object
        placemark = kml.Placemark()

        # Assign the LineString geometry to the place mark
        # TODO: correct (geometry property cannot be set)
        placemark.geometry = linestring_geometry

        # Add the place mark to the KML Document
        document.append(placemark)

    # Return the KML Document as a string
    return k.to_string(prettyprint=True)


if __name__ == '__main__':
    segment_dict = parse_ttl_for_horizontal_segments(
        '/Users/airymagnien/PycharmProjects/SemanticRSM/Code/Import/SD1_import/scheibenberg.ttl', arcs_only=False)
    wkts = generate_wkt(segment_dict)
    kml_data = linestrings_to_kml(wkts)
    with open('/Users/airymagnien/PycharmProjects/SemanticRSM/Code/Export/scheibenberg_all.kml', 'w') as file:
        file.write(kml_data)
