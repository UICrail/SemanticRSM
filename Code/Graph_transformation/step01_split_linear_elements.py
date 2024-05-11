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

from shapely.geometry import LineString
from shapely.wkt import dumps
from Code.Namespaces import *


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
    shared_coords = find_shared_intermediate_points(linestring_dict)
    new_elements = split_linestrings(linestring_dict, shared_coords)
    path_to_split = "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/"
    generate_turtle_from_linestrings(new_elements, path_to_split + f"osm_{short_name_}_split.ttl")
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
    for s, _, o in g.triples((None, RDF.type, RSM_TOPOLOGY.LinearElement)):
        wkt = g.value(s, GSP.asWKT)
        if wkt:
            linestring_dict[s] = shapely.wkt.loads(str(wkt))
    return linestring_dict


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

    # Then drop the points that correspond to two or more elements joint at their extremity
    shared = {coord: uris for coord, uris in shared.items() if set(uris) != {'extremity'}}

    # Finally, remove the 'extremity' placeholders

    shared = {coord: [uri for uri in uris if uri != 'extremity'] for coord, uris in shared.items()}

    return shared


def split_linestrings(linestrings: dict[URIRef, LineString], shared_coords: dict[str, list[URIRef]],
                      verbose: bool = False):
    """
    Split elements at intermediate points in linestrings when these points are shared between two or more elements.
    :param linestrings:
    :param shared_coords:
    :param verbose: if True, each split linestring will be reported
    :return: None
    """
    linestrings_to_remove = set()
    linestrings_to_add = dict()

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
    print(f"Split : number of raw linestrings before splitting: {len(linestrings)}")
    for ls in linestrings_to_remove:
        del linestrings[ls]
    print(f"Split : number of linestrings to remove: {len(linestrings_to_remove)}")
    print(f"Split : remaining linestrings: {len(linestrings)}")
    # ... and add the splits
    print(f"Split : linestrings to be added: {len(linestrings_to_add)}")
    for k, v in linestrings_to_add.items():
        linestrings[k] = v
    print(f"Split : resulting linestrings: {len(linestrings)}")

    return linestrings


def generate_turtle_from_linestrings(modified_linestrings: dict[str, LineString], output_file_path: str):
    """

    :param modified_linestrings:
    :param output_file_path:
    :return:
    """

    # Initialize the RDF graph
    g = rdflib.Graph()

    # Bind the namespaces
    g.bind("gsp", GSP)
    g.bind("rsm", RSM_TOPOLOGY)
    g.bind("", WORK)

    for uri, linestring in modified_linestrings.items():
        # Ensure the geometry is a LineString
        if not isinstance(linestring, LineString):
            continue
        uri_ref = URIRef(uri)

        # Convert the LineString to WKT
        wkt = dumps(linestring)
        wkt_literal = Literal(wkt, datatype=GSP.wktLiteral)

        # Create the triples
        g.add((uri_ref, RDF.type, RSM_TOPOLOGY.LinearElement))  # Type of the element
        g.add((uri_ref, RDF.type, GSP.Geometry))  # ...also of type: Geometry
        g.add((uri_ref, GSP.asWKT, wkt_literal))  # Geometry representation using Well-Known Text (WKT)

    # Serialize the graph to the Turtle file
    g.serialize(destination=output_file_path, format='turtle')
    print(f"Generated Turtle file: {output_file_path}")


if __name__ == "__main__":
    from Code.Export.export_to_kml import ttl_to_kml

    short_name = "Ventimiglia-Albenga"

    ttl_to_kml(
        f"/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{short_name}_raw.ttl",
        f"/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/Intermediate_files/osm_{short_name}_split.kml")
