from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
from shapely import LineString
from shapely.geometry import Point
from shapely.wkt import loads, dumps
from shapely.ops import linemerge
from collections import Counter
from typing import Dict, List, Optional, Set
from Code.Namespaces import *


def add_ports(input_ttl: str, output_ttl: Optional[str] = None) -> None:
    g = Graph()
    g.parse(input_ttl, format='turtle')

    linear_element_count = len(list(g.subjects(RDF.type, RSM_TOPOLOGY.LinearElement)))

    print(f"Creating ports at the extremities of {linear_element_count} linear elements:")

    counter=0

    for linear_element in g.subjects(RDF.type, RSM_TOPOLOGY.LinearElement):
        # Get extremal coordinates
        geometry = loads(str(g.value(linear_element, GEO.asWKT)))
        extr0, extr1 = Point(geometry.coords[0]), Point(geometry.coords[-1])
        uri0, uri1 = URIRef(str(linear_element) + '_0'), URIRef(str(linear_element) + '_1')
        # Create the two ports
        g.add((URIRef(uri0), RDF.type, RSM_TOPOLOGY.Port))
        g.add((URIRef(uri1), RDF.type, RSM_TOPOLOGY.Port))
        # Their geometry
        g.add((URIRef(uri0), GEO.asWKT, Literal(extr0)))
        g.add((URIRef(uri1), GEO.asWKT, Literal(extr1)))
        # Add the relationship between the linear element and the ports
        g.add((linear_element, RSM_TOPOLOGY.hasPort, uri0))
        g.add((linear_element, RSM_TOPOLOGY.hasPort, uri1))
        counter += 1

    print(f"{counter} pairs of ports were created.")

    if linear_element_count != counter:
        print("WARNING: there seems to be a mismatch above.")

    # Output
    if output_ttl:
        g.serialize(destination=output_ttl, format='turtle')
    else:
        print(g.serialize(format='turtle').decode())
