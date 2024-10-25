"""
Purpose is to split linear elements (linestrings) where they have an intermediate point that is also present
in any other linestring.
The procedure is simplistic, and not optimized for efficiency:
probably O(Nˆ2), N being the number of coord pairs in linestrings.
Consider using spatial indexing in an improved version.

Checked for correctness, 9/4/2024: output seems OK as the splits indeed have a common point at some extremity.
Not thoroughly checked for exhaustiveness, but looks OK too.
"""

from typing import List

import rdflib
import shapely
from rdflib import RDF, Literal, URIRef
from shapely.geometry import LineString
from shapely.wkt import dumps

from Code.Namespaces import *
from Graph_transformation.graph_file_handing import _load_graph


def split_linestrings_in_file(file_path: str, short_name_: str = "", with_kml: bool = False):
    """
    Splits linestrings where they share a common point (except at extremities).
    :param file_path: input file path
    :param short_name_: will be used for naming the output ttl file
    :param with_kml: if True, a kml representation of the ttl file will be generated.
    :return: None
    """
    print("splitting the Turtle file: ", file_path)
    linestring_dict = parse_turtle_for_linear_element_geometry(file_path)
    label_dict = parse_turtle_for_labels(file_path)
    shared_coords = find_shared_intermediate_points(linestring_dict)
    modified_linestrings = split_linestrings(linestring_dict, shared_coords)
    path_to_split = "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/"
    generate_turtle_from_linestrings(file_path, modified_linestrings[0], modified_linestrings[1],
                                     path_to_split + f"osm_{short_name_}_split.ttl", label_dict)
    if with_kml:
        ttl_to_kml(path_to_split + f"osm_{short_name_}_split.ttl", path_to_split + f"osm_{short_name_}_split.kml")


def parse_turtle_for_linear_element_geometry(file_path: str) -> dict[URIRef, LineString]:
    """
    retrieves WKT strings from file
    :returns dictionary with key = URL, value = WKT string
    """
    g = rdflib.Graph()
    g.parse(file_path, format="turtle")

    linestring_dict = {}
    for s, _, o in g.triples((None, RDF.type, RSM_GEOSPARQL_ADAPTER.Geometry)):
        wkt = g.value(s, GEOSPARQL.asWKT)
        if wkt:
            linestring_dict[s] = shapely.wkt.loads(str(wkt))
        # TODO: this looks unnecessarily awkward.
    return linestring_dict


def parse_turtle_for_labels(file_path: str) -> dict[URIRef, Literal]:
    g = rdflib.Graph()
    g.parse(file_path, format="turtle")
    label_dict = {}
    for s, _, o in g.triples((None, RDFS.label, None)):
        label_dict[s] = o
    return label_dict


# checked 1/5/2024
def find_shared_intermediate_points(elements: dict[URIRef, LineString]) -> dict[str, list[URIRef | str]]:
    """
    Identify intermediate points in the linestrings ("ls") that are shared between two or more line strings.
    The returned dictionary maps points to a list of URIRefs of Linear Elements that share the same point.
    When the shared point is at an extremity of another element, URIRef is replaced by 'extremity'
    (since we will not split an element at its extremity...)
    """
    shared: dict[str, List[URIRef | str]] = {}  # where the first "str" is the POINT WKT coordinate tuple

    # First, scan through all elements and put all coords into the dictionary:

    for uri, ls in elements.items():
        max_index = len(list(ls.coords)) - 1
        for count, coord in enumerate(ls.coords):
            if coord not in shared:
                shared[coord] = []
            if 0 < count < max_index:
                # append URI of element that has the coord at some intermediate place
                shared[coord].append(uri)
            else:
                shared[coord].append('extremity')

    # Drop those coords that only occur once (and that's a lot)

    shared = {coord: uris for coord, uris in shared.items() if len(uris) > 1}

    # Then drop the points that correspond to two or more elements joint at their extremities only
    shared = {coord: uris for coord, uris in shared.items() if set(uris) != {'extremity'}}

    # Finally, remove the 'extremity' placeholders
    shared = {coord: [uri for uri in uris if uri != 'extremity'] for coord, uris in shared.items()}

    return shared


def split_linestrings(linestrings: dict[URIRef, LineString], shared_coords: dict[str, list[URIRef]],
                      verbose: bool = False) -> (dict[URIRef, LineString], set[URIRef]):
    """
    Split elements at intermediate points in linestrings when these points are shared between two or more elements.
    :param linestrings: original linestrings dictionary
    :param shared_coords: dict of coordinates shared between two or more linear elements,
    where the coordinate does not correspond to an extremity in at least one case.
    :param verbose: if True, each split linestring will be reported.
    :return: (modified (split) linestrings dictionary, set of linestrings to be suppressed)
    """
    linestrings_to_remove = set()
    linestrings_to_add = {}

    for uri, ls in linestrings.items():
        ls_coords = list(ls.coords)
        ls_split_at = []
        for coord, uri_list in shared_coords.items():
            if uri in uri_list:
                ls_split_at.append(coord)
        if ls_split_at:  # test for non-empty list
            part_index: int = 0
            tail = ls_coords
            for coord in ls_coords:
                if coord in ls_split_at:
                    head = tail[:tail.index(coord) + 1]
                    new_tail = tail[tail.index(coord):]
                    linestrings_to_add[URIRef(f"{uri}_part_{part_index}")] = LineString(head)
                    part_index += 1
                    tail = new_tail
            linestrings_to_add[URIRef(f"{uri}_part_{part_index}")] = LineString(tail)
            linestrings_to_remove.add(URIRef(uri))
            if verbose:
                print(f"linestring {uri} was split into {part_index + 1} parts")

    # Lastly, remove all split linestrings
    print("Splitting linestrings, to avoid any branches from inside a Linear Element")
    print(f"    number of linestrings before splitting: {len(linestrings)}")
    print(f"    number of linestrings to remove: {len(linestrings_to_remove)}")
    print(f"    number of linestrings to add: {len(linestrings_to_add)}")

    return linestrings_to_add, linestrings_to_remove


def generate_turtle_from_linestrings(file_path: str, linestrings_to_add: dict[URIRef, LineString],
                                     linestrings_to_remove: set[URIRef], output_file_path: str, label_dict: dict = None):
    """
    Modifies the linear elements according to the split linestrings and stores result in ttl file.
    :param label_dict: dictionary of labels key = linear element URI ref, value = Literal
    :param linestrings_to_remove:
    :param linestrings_to_add:
    :param file_path: turtle file with linear elements and their geometries
    :param output_file_path: to ttl file
    :return: None
    """

    # Load the RDF graph
    graph = _load_graph(file_path)

    # Bind the namespaces
    graph.bind("geo", GEOSPARQL)
    graph.bind("rsm", RSM_TOPOLOGY)
    graph.bind("rsm", RSM_GEOSPARQL_ADAPTER)
    graph.bind("", WORK)

    # Handle the geometries (linestrings)

    for geom_uri, linestring in linestrings_to_add.items():
        # Convert the LineString to WKT
        wkt = dumps(linestring)
        wkt_literal = Literal(wkt, datatype=GEOSPARQL.wktLiteral)

        # Create the triples for geometries
        graph.add((geom_uri, RDF.type, RSM_GEOSPARQL_ADAPTER.Geometry))
        graph.add((geom_uri, GEOSPARQL.asWKT, wkt_literal))  # Geometry representation using Well-Known Text (WKT)

    # Handle the features (linear elements)

    count_lines, count_geometries = 0, 0

    for geom_uri in linestrings_to_add:
        index = geom_uri.split('_', 1)[1]
        line_uri = URIRef(WORK + 'split_line' + '_' + index)
        graph.add((line_uri, RDF.type, RSM_TOPOLOGY.LinearElement))
        graph.add((line_uri, RSM_GEOSPARQL_ADAPTER.hasNominalGeometry, geom_uri))
        if label_dict.get(line_uri):
            graph.add((line_uri, RDFS.label, label_dict[line_uri]))
        count_lines += 1
        count_geometries += 1

    print(f"    Generated {count_lines} linear elements and {count_geometries} nominal geometry properties")
    lines_to_remove = set()

    count_lines = 0
    for linestring in linestrings_to_remove:
        for matching_line in graph.subjects(RSM_GEOSPARQL_ADAPTER.hasNominalGeometry, linestring):
            lines_to_remove.add(matching_line)
            count_lines += 1
    print(f"    Number of linear elements removed (matching the geometries to be removed): {count_lines}")

    count_lines: int = 0
    for line_to_remove in lines_to_remove:
        graph.remove((line_to_remove, None, None))
        graph.remove((None, None, line_to_remove))
        count_lines += 1
    print(f"    Removed {count_lines} linear elements")

    # finally, remove the triples referring to obsolete geometries, if any

    for geo_uri in linestrings_to_remove:
        graph.remove((geo_uri, None, None))
        graph.remove((None, None, geo_uri))

    # Serialize the graph to the Turtle file
    graph.serialize(destination=output_file_path, format='turtle')
    print(f"Generated Turtle file: {output_file_path}")


if __name__ == "__main__":
    from Code.Export.export_wkt_to_kml import ttl_to_kml

    short_name = "Ventimiglia-Albenga"

    ttl_to_kml(
        f"/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{short_name}_raw.ttl",
        f"/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{short_name}_split.kml")
