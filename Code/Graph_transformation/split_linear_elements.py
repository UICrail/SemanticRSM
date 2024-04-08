"""
Purpose is to split linear elements (linestrings) where they have an intermediate point that is also present
in any other linestring.
The procedure is simplistic, and not optimized for efficiency:
probably O(Nˆ2), N being the number of coord pairs in linestrings.
Consider using spatial indexing in an improved version.
"""

from collections import defaultdict
import rdflib
from rdflib import RDF, Literal
from rdflib.namespace import Namespace
import shapely
from shapely.geometry import LineString
from shapely.wkt import dumps

# Define your namespaces
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
RSM = Namespace("http://www.example.org/rsm#")


def split_linear_elements(file_path):
    print("splitting the Turtle file: ", file_path)
    elements = parse_turtle(file_path)
    shared_coords = find_shared_coordinates(elements)
    new_elements = element_split(elements, shared_coords)
    generate_turtle_from_elements(new_elements,
                "/Users/airymagnien/PycharmProjects/SemanticRSM/Intermediate_files/osm_railways_split.ttl")

    # Further processing to save new_elements back to a Turtle file can be added here.
    # This involves converting the LineStrings back to WKT and creating RDF triples.


def parse_turtle(file_path):
    g = rdflib.Graph()
    g.parse(file_path, format="turtle")

    elements = {}
    for s, _, o in g.triples((None, RDF.type, RSM.LinearElement)):
        wkt = g.value(s, GEO.asWKT)
        if wkt:
            elements[s] = shapely.wkt.loads(str(wkt))
    return elements


def find_shared_coordinates(elements):
    """Identify shared coordinates that are intermediate points in the linestrings."""
    coord_count = defaultdict(int)
    for ls in elements.values():
        # Consider only intermediate points
        for coord in list(ls.coords)[1:-1]:
            coord_count[coord] += 1

    shared_coords = {coord for coord, count in coord_count.items() if count >= 3}
    return shared_coords


def element_split(elements, shared_coords):
    """Split elements at shared coordinates and remove original elements if split."""
    new_elements = {}
    elements_to_remove = set()
    split_counter = 0

    for uri, ls in elements.items():
        split_points = [coord for coord in shared_coords if coord in list(ls.coords)[1:-1]]
        if not split_points:
            # If there are no split points, keep the element as is
            new_elements[uri] = ls
            continue

        # Track elements that will be split, so they can be removed
        elements_to_remove.add(uri)

        # Split the LineString at each split point
        # Note: This example assumes a single split point for simplicity
        for split_point in split_points:
            split_index = list(ls.coords).index(split_point)
            part1 = LineString(ls.coords[:split_index + 1])
            part2 = LineString(ls.coords[split_index:])

            # Add the new parts as new elements
            new_elements[f"{uri}_part1"] = part1
            new_elements[f"{uri}_part2"] = part2
            split_counter += 1

    # Remove the original elements that have been split
    for uri in elements_to_remove:
        if uri in new_elements:
            del new_elements[uri]

    print("split count: ", split_counter)
    return new_elements


def generate_turtle_from_elements(new_elements, output_file):
    # Initialize the RDF graph
    g = rdflib.Graph()

    # Bind the namespaces
    g.bind("geo", GEO)
    g.bind("rsm", RSM)

    for uri, linestring in new_elements.items():
        # Ensure the geometry is a LineString
        if not isinstance(linestring, LineString):
            continue

        # Convert the LineString to WKT
        wkt = dumps(linestring)
        wkt_literal = Literal(wkt, datatype=GEO.wktLiteral)

        # Create the triples
        g.add((uri, RDF.type, RSM.LinearElement))  # Type of the element
        g.add((uri, RDF.type, GEO.Geometry))  # Subclass of Geometry
        g.add((uri, GEO.asWKT, wkt_literal))  # Geometry representation

    # Serialize the graph to the Turtle file
    g.serialize(destination=output_file, format='turtle')
    print(f"Generated Turtle file: {output_file}")
