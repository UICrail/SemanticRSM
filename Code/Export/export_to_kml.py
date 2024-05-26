from rdflib import URIRef
from rdflib.namespace import RDF, Namespace
from shapely.wkt import loads
from shapely.geometry import LineString
from typing import Dict, List
from Code.Namespaces import *


def ttl_to_kml(input_ttl_, output_kml_):
    elements = parse_ttl_to_linestrings(input_ttl_)
    adjacency_list = build_adjacency_list(elements)
    element_colors = color_elements(adjacency_list)
    generate_kml_from_elements_and_colors(elements, element_colors, output_kml_)
    print(f"KML file generated: {output_kml_}")


def parse_ttl_to_linestrings(input_ttl_: str) -> Dict[URIRef, LineString]:
    from rdflib import Graph

    g = Graph()
    g.parse(input_ttl_, format="turtle")

    elements: Dict[URIRef, LineString] = {}
    for s, _, o in g.triples((None, GEOSPARQL.asWKT, None)):
        if (s, RDF.type, RSM_TOPOLOGY.LinearElement) in g:
            geom = loads(str(o))
            if isinstance(geom, LineString):
                elements[s] = geom
    return elements


def generate_kml_from_elements_and_colors(elements: Dict[URIRef, LineString], colors: Dict[URIRef, str],
                                          output_kml_: str) -> None:
    import simplekml

    kml = simplekml.Kml()
    for uri, geom in elements.items():
        linestring = kml.newlinestring(name=str(uri), coords=[(pt[0], pt[1]) for pt in geom.coords])
        linestring.style.linestyle.color = colors[uri]
        linestring.style.linestyle.width = 4  # Adjust width as needed
    kml.save(output_kml_)


def build_adjacency_list(elements: Dict[URIRef, LineString]) -> Dict[URIRef, List[URIRef]]:
    adjacency_dict = {uri: [] for uri in elements.keys()}
    endpoints = {}
    for uri, geom in elements.items():
        for point in [geom.coords[0], geom.coords[-1]]:
            if point in endpoints:
                for adjacent_uri in endpoints[point]:
                    adjacency_dict[uri].append(adjacent_uri)
                    adjacency_dict[adjacent_uri].append(uri)
                endpoints[point].append(uri)
            else:
                endpoints[point] = [uri]
    return adjacency_dict


def color_elements(adjacency_list: Dict[URIRef, List[URIRef]]) -> Dict[URIRef, str]:
    """
    Assigns colors to elements based on adjacency, ensuring no adjacent elements share the same color.
    Uses hexadecimal color codes, with black as a fallback if all other colors are in use.

    :param adjacency_list: A dictionary representing the adjacency list of the elements,
                           where keys are element URIs (as URIRef) and values are lists of URIs (as URIRef)
                           of adjacent elements.
    :return: A dictionary mapping element URIs (as URIRef) to their assigned hexadecimal color codes.
    """
    colors = ['ff0000aa', 'ff00ff00', 'ffff0000', 'ff800080']  # Dark Red, Green, Blue, Purple
    element_colors: Dict[URIRef, str] = {}

    for element in adjacency_list.keys():
        used_colors = {element_colors.get(adjacent) for adjacent in adjacency_list[element]}
        for color in colors:
            if color not in used_colors:
                element_colors[element] = color
                break
        else:
            # If all predefined colors are used, assign 'yellow'
            element_colors[element] = 'ffffff00'

    return element_colors
