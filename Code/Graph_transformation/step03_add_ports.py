from typing import Optional

from pyproj import Geod
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
from shapely.geometry import Point
from shapely.wkt import loads

from Code.Namespaces import *

wgs84_geod = Geod(ellps='WGS84')


def add_ports(input_ttl: str, output_ttl: Optional[str] = None, with_inverse_properties: bool = True) -> None:
    g = Graph()
    g.parse(input_ttl, format='turtle')

    linear_element_count = len(list(g.subjects(RDF.type, RSM_TOPOLOGY.LinearElement)))

    print(f"\nCreating ports at the extremities of {linear_element_count} linear elements:")

    counter = 0

    for linear_element in g.subjects(RDF.type, RSM_TOPOLOGY.LinearElement):
        # Get extremal coordinates
        geometry = g.value(linear_element, RSM_GEOSPARQL_ADAPTER.hasNominalGeometry)
        wkt = loads(str(g.value(geometry, GEOSPARQL.asWKT)))
        extr0, extr1 = Point(wkt.coords[0]), Point(wkt.coords[-1])
        next0, next1 = Point(wkt.coords[1]), Point(wkt.coords[-2])
        # azimuths (pyproj yields azimuths in the -180 to +180 range)
        az0 = wgs84_geod.inv(next0.x, next0.y, extr0.x, extr0.y)[0]
        az1 = wgs84_geod.inv(next1.x, next1.y, extr1.x, extr1.y)[0]
        uri0, uri1 = URIRef(str(linear_element) + '_port_0'), URIRef(str(linear_element) + '_port_1')
        # Create the two ports...
        g.add((URIRef(uri0), RDF.type, RSM_TOPOLOGY.Port))
        g.add((URIRef(uri1), RDF.type, RSM_TOPOLOGY.Port))
        # ... their geometry
        g.add((URIRef(uri0), GEOSPARQL.asWKT, Literal(extr0)))
        g.add((URIRef(uri1), GEOSPARQL.asWKT, Literal(extr1)))
        # ... their azimuth (outward azimuth; range -180 to 180 wrt North)
        g.add((URIRef(uri0), RSM_TOPOLOGY.azimuth, Literal(az0)))
        g.add((URIRef(uri1), RSM_TOPOLOGY.azimuth, Literal(az1)))
        # Add the relationship between the linear element and the ports
        g.add((linear_element, RSM_TOPOLOGY.hasPort, uri0))
        g.add((linear_element, RSM_TOPOLOGY.hasPort, uri1))
        if with_inverse_properties:
            g.add((uri0, RSM_TOPOLOGY.onElement, linear_element))
            g.add((uri1, RSM_TOPOLOGY.onElement, linear_element))
        counter += 1

    print(f"    {counter} pairs of ports were created.")

    if linear_element_count != counter:
        print("    WARNING: there seems to be a mismatch above.")

    # Output
    if output_ttl:
        g.serialize(destination=output_ttl, format='turtle')
    else:
        print(g.serialize(format='turtle'))
