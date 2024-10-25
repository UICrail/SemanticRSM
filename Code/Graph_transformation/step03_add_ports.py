from typing import Optional
from pyproj import Geod
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
from shapely.geometry import Point
from shapely.wkt import loads
from Code.Namespaces import *

wgs84_geod = Geod(ellps='WGS84')

PORT_SUFFIX_0 = '_port_0'
PORT_SUFFIX_1 = '_port_1'


def create_port(graph: Graph, linear_element: URIRef, extremity: Point, azimuth: float, port_suffix: str):
    port_uri = URIRef(str(linear_element) + port_suffix)
    graph.add((port_uri, RDF.type, RSM_TOPOLOGY.Port))
    graph.add((port_uri, GEOSPARQL.asWKT, Literal(extremity)))
    graph.add((port_uri, RSM_TOPOLOGY.azimuth, Literal(azimuth)))
    graph.add((linear_element, RSM_TOPOLOGY.hasPort, port_uri))
    return port_uri


def add_ports_to_linear_elements(input_ttl: str, output_ttl: Optional[str] = None,
                                 with_inverse_properties: bool = True) -> None:
    from Graph_transformation.graph_file_handing import _load_graph
    graph = _load_graph(input_ttl)
    linear_element_count = len(list(graph.subjects(RDF.type, RSM_TOPOLOGY.LinearElement)))
    print(f"\nCreating ports at the extremities of {linear_element_count} linear elements:")
    counter = 0

    for linear_element in graph.subjects(RDF.type, RSM_TOPOLOGY.LinearElement):
        geometry = graph.value(linear_element, RSM_GEOSPARQL_ADAPTER.hasNominalGeometry)
        wkt = loads(str(graph.value(geometry, GEOSPARQL.asWKT)))
        extremity0, extremity1 = Point(wkt.coords[0]), Point(wkt.coords[-1])
        neighbor0, neighbor1 = Point(wkt.coords[1]), Point(wkt.coords[-2])

        azimuth0 = wgs84_geod.inv(neighbor0.x, neighbor0.y, extremity0.x, extremity0.y)[0]
        azimuth1 = wgs84_geod.inv(neighbor1.x, neighbor1.y, extremity1.x, extremity1.y)[0]

        port_uri0 = create_port(graph, linear_element, extremity0, azimuth0, PORT_SUFFIX_0)
        port_uri1 = create_port(graph, linear_element, extremity1, azimuth1, PORT_SUFFIX_1)

        if with_inverse_properties:
            graph.add((port_uri0, RSM_TOPOLOGY.onElement, linear_element))
            graph.add((port_uri1, RSM_TOPOLOGY.onElement, linear_element))

        counter += 1

    print(f"    {counter} pairs of ports were created.")
    if linear_element_count != counter:
        print("    WARNING: there seems to be a mismatch above.")

    from Graph_transformation.graph_file_handing import _save_graph
    _save_graph(graph, output_ttl)
