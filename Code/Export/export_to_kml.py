from rdflib import URIRef
from rdflib.namespace import RDF, Namespace
from shapely.wkt import loads
from shapely.geometry import LineString
from typing import Dict, List

GEO = Namespace("http://www.opengis.net/ont/geosparql#")
RSM = Namespace("http://www.example.org/rsm#")

# Assuming the `build_adjacency_list` and `color_elements` functions are defined as previously

# Example usage
input_ttl = 'input.ttl'  # Update this path to your Turtle file
output_kml = 'output.kml'  # Update this path to your desired output KML file


def ttl_to_kml(input_ttl, output_kml):
    elements = parse_ttl_to_linestrings(input_ttl)
    adjacency_list = build_adjacency_list(elements)
    element_colors = color_elements(elements, adjacency_list)
    generate_kml_from_elements_and_colors(elements, element_colors, output_kml)
    print(f"KML file generated: {output_kml}")


def parse_ttl_to_linestrings(input_ttl: str) -> Dict[URIRef, LineString]:
    from rdflib import Graph

    g = Graph()
    g.parse(input_ttl, format="turtle")

    elements = {}
    for s, _, o in g.triples((None, GEO.asWKT, None)):
        if (s, RDF.type, RSM.LinearElement) in g:
            geom = loads(str(o))
            if isinstance(geom, LineString):
                elements[s] = geom
    return elements


def generate_kml_from_elements_and_colors(elements: Dict[URIRef, LineString], colors: Dict[URIRef, str],
                                          output_kml: str) -> None:
    import simplekml

    kml = simplekml.Kml()
    for uri, geom in elements.items():
        linestring = kml.newlinestring(name=str(uri), coords=[(pt[0], pt[1]) for pt in geom.coords])
        linestring.style.linestyle.color = colors[uri]
        linestring.style.linestyle.width = 2  # Adjust width as needed
    kml.save(output_kml)


def build_adjacency_list(elements: Dict[URIRef, LineString]) -> Dict[URIRef, List[URIRef]]:
    adjacency_list = {uri: [] for uri in elements.keys()}
    adjacency_list = {uri: [] for uri in elements.keys()}
    endpoints = {}
    for uri, geom in elements.items():
        for point in [geom.coords[0], geom.coords[-1]]:
            if point in endpoints:
                for adjacent_uri in endpoints[point]:
                    adjacency_list[uri].append(adjacent_uri)
                    adjacency_list[adjacent_uri].append(uri)
                endpoints[point].append(uri)
            else:
                endpoints[point] = [uri]
    return adjacency_list


def color_elements(elements: Dict[URIRef, LineString], adjacency_list: Dict[URIRef, List[URIRef]]) -> Dict[URIRef, str]:
    colors = ['ff0000ff', 'ff00ff00', 'ffff0000', 'ff800080']  # Red, Green, Blue, Purple
    element_colors = {}
    for uri in elements.keys():
        available_colors = set(colors)
        for neighbor in adjacency_list[uri]:
            if neighbor in element_colors:
                available_colors.discard(element_colors[neighbor])
        element_colors[uri] = available_colors.pop()  # Assign the first available color
    return element_colors
