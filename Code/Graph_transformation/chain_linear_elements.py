import rdflib.graph
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import Namespace, RDF
from typing import Tuple, Optional, Dict
from shapely.geometry import LineString
from shapely.wkt import loads, dumps

GEO = Namespace("http://www.opengis.net/ont/geosparql#")
RSM = Namespace("http://www.example.org/rsm#")


def reverse_linestring(geom: LineString) -> LineString:
    """
    Returns a new LineString geometry with reversed coordinates.
    """
    return LineString(list(geom.coords)[::-1])


def can_chain(geom_x: LineString, geom_y: LineString) -> Optional[Tuple[bool, bool]]:
    """
    Determines if two geometries can be chained.
    Returns a tuple (chain_x_to_y, reverse_y_before_chaining) indicating whether
    X can be chained to Y and whether Y should be reversed before chaining.
    """
    if geom_x.coords[-1] == geom_y.coords[0]:
        return True, False
    elif geom_x.coords[0] == geom_y.coords[-1]:
        return False, True
    elif geom_x.coords[0] == geom_y.coords[0]:
        return True, True
    elif geom_x.coords[-1] == geom_y.coords[-1]:
        return False, False
    return None


def regenerate_elements(gr: rdflib.graph.Graph) -> Dict[URIRef, LineString]:
    elements: Dict[URIRef, LineString] = {}
    for s, _, o in gr.triples((None, GEO.asWKT, None)):
        if (s, RDF.type, RSM.LinearElement) in gr:
            elements[s] = loads(str(o))
    return elements


def chain_linear_elements(input_ttl: str, output_ttl: str) -> None:
    """Extremely inefficient, but hopefully correct"""
    g = Graph()
    g.parse(input_ttl, format="turtle")

    elements = regenerate_elements(g)

    chained = set()
    chain_counter = 0
    for uri_x, geom_x in elements.items():
        if uri_x in chained:
            continue
        for uri_y, geom_y in elements.items():
            if uri_y in chained or uri_y == uri_x:
                continue

            chaining_info = can_chain(geom_x, geom_y)
            if chaining_info:
                chain_x_to_y, reverse_y = chaining_info

                # Prepare Y by reversing if necessary
                geom_y_prepared = reverse_linestring(geom_y) if reverse_y else geom_y

                # Chain X to Y or Y to X based on the direction
                if chain_x_to_y:
                    new_geom = LineString(list(geom_x.coords) + list(geom_y_prepared.coords)[1:])
                else:
                    new_geom = LineString(list(geom_y_prepared.coords) + list(geom_x.coords)[1:])

                # Update X with new geometry and mark Y for removal
                g.set((uri_x, GEO.asWKT, Literal(dumps(new_geom), datatype=GEO.wktLiteral)))
                chained.add(uri_y)
                chain_counter += 1
                # Remove the original elements that have been chained
                g.remove((uri_y, None, None))
                g.remove((uri_y, RDF.type, RSM.LinearElement))
                g.remove((uri_y, GEO.asWKT, None))
                regenerate_elements(g)
                break

    g.serialize(destination=output_ttl, format='turtle')
    print(f'Chained {chain_counter} linear elements')
    print(f"Chained Turtle file generated: {output_ttl}")
