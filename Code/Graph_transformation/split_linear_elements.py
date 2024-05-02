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
from rdflib import RDF, Literal, URIRef

import shapely
from rdflib.term import Node
from shapely.geometry import LineString
from shapely.wkt import dumps
from Code.Namespaces import *


def split_linear_elements(file_path: str, short_name: str = ""):
    print("splitting the Turtle file: ", file_path)
    elements = parse_turtle(file_path)
    shared_coords = find_shared_intermediate_points(elements)
    new_elements = split_elements(elements, shared_coords)
    generate_turtle_from_elements(new_elements,
                                  "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{}_split.ttl".format(
                                      short_name))


def parse_turtle(file_path: str) -> dict[Node, str]:
    g = rdflib.Graph()
    g.parse(file_path, format="turtle")

    elements = {}
    for s, _, o in g.triples((None, RDF.type, RSM_TOPOLOGY.LinearElement)):
        wkt = g.value(s, GEO.asWKT)
        if wkt:
            elements[s] = shapely.wkt.loads(str(wkt))
    return elements


# checked 1/5/2024
def find_shared_intermediate_points(elements) -> dict[str, List[URIRef | str]]:
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

    # Then drop the points that correspond to two or more elements joint at their extremity
    shared = {coord: uris for coord, uris in shared.items() if set(uris) != {'extremity'}}

    # Finally, remove the 'extremity' placeholders

    shared = {coord: [uri for uri in uris if uri != 'extremity'] for coord, uris in shared.items()}

    return shared


def split_elements(elements, shared_coords: dict[str, List[URIRef]]):
    """
    Split elements at intermediate points in linestrings when these points are shared between two or more elements.
    :param elements:
    :param shared_coords:
    :return:
    """
    elements_to_remove = set()

    for split_point, uris in shared_coords.items():
        for uri in uris:
            if uri in elements:
                coords = list(elements[uri].coords)
                split_index = coords.index(split_point)
                part1 = LineString(coords[:split_index + 1])
                part2 = LineString(coords[split_index:])
                elements[f"{uri}_part1"] = part1
                elements[f"{uri}_part2"] = part2
                elements_to_remove.add(uri)

    # finally, do the cleanup
    for uri in elements_to_remove:
        if uri in elements:
            del elements[uri]

    return elements


def generate_turtle_from_elements(new_elements, output_file: str):
    # Initialize the RDF graph
    g = rdflib.Graph()

    # Bind the namespaces
    g.bind("geo", GEO)
    g.bind("rsm", RSM_TOPOLOGY)

    for uri, linestring in new_elements.items():
        # Ensure the geometry is a LineString
        if not isinstance(linestring, LineString):
            continue
        uri_ref = URIRef(uri)

        # Convert the LineString to WKT
        wkt = dumps(linestring)
        wkt_literal = Literal(wkt, datatype=GEO.wktLiteral)

        # Create the triples
        g.add((uri_ref, RDF.type, RSM_TOPOLOGY.LinearElement))  # Type of the element
        g.add((uri_ref, RDF.type, GEO.Geometry))  # Subclass of Geometry
        g.add((uri_ref, GEO.asWKT, wkt_literal))  # Geometry representation

    # Serialize the graph to the Turtle file
    g.serialize(destination=output_file, format='turtle')
    print(f"Generated Turtle file: {output_file}")


if __name__ == "__main__":
    from Code.Export.export_to_kml import ttl_to_kml

    ttl_to_kml("/Users/airymagnien/PycharmProjects/SemanticRSM/Intermediate_files/osm_railways_raw.ttl",
               "/Users/airymagnien/PycharmProjects/SemanticRSM/Intermediate_files/osm_railways_split.kml")
