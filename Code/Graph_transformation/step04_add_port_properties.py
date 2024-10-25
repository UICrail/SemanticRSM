import itertools
from typing import Optional

from rdflib import Graph
from rdflib.namespace import RDF
from rdflib.term import Node

from Code.Namespaces import *
from Graph_transformation.geometry_scrutiny import deviation_angle, possible_navigability


def set_port_connections(input_ttl: str, output_ttl: Optional[str] = None):
    g = Graph()
    g.parse(input_ttl, format="turtle")

    print("Setting the connections between ports")

    # Get all the ports in the graph
    ports = g.subjects(RDF.type, RSM_TOPOLOGY.Port)  # a generator
    list_ports = list(itertools.islice(ports, None))
    print(f"    {len(list_ports)} ports found")

    # Iterate over each port
    connections_count = 0
    for index, port1 in enumerate(list_ports[:-2]):
        c1 = g.value(port1, GEOSPARQL.asWKT)
        for port2 in list_ports[index + 1:]:
            c2 = g.value(port2, GEOSPARQL.asWKT)
            if c1 == c2:
                g.add((port1, RSM_TOPOLOGY.connectedWith, port2))
                connections_count += 1

    print(f"    {connections_count} ports connected")

    # Output
    if output_ttl:
        g.serialize(destination=output_ttl, format='turtle')
        print(f"Ports are now connected. All data saved to {output_ttl}.")
    else:
        print(g.serialize(format='turtle'))


def get_opposite_port(graph: Graph, port: Node) -> Node | None:
    """
    Looks for the opposite port in a linear element. If the given port is not a linear element,
    returns None.
    :param graph the RDF graph
    :param port a port node in the graph that is supposed to belong to a single linear element
    :returns the opposite port, or None if the element is not a Linear Element
    """
    elements = list(graph.objects(port, RSM_TOPOLOGY.onElement))  # only one element is expected; better check:
    assert len(elements) == 1, "ERROR: port {} belongs to more than one element, namely {} ".format(port,
                                                                                                    elements)
    element = elements[0]
    other_ports = []
    if graph.value(element, RDF.type) == RSM_TOPOLOGY.LinearElement:
        other_ports = [x for x in graph.subjects(RSM_TOPOLOGY.onElement, element) if x != port]
    else:
        print(f"**** WARNING: looking for an opposite port on non-linear element {element}")
    return other_ports[0] if other_ports else None


def set_navigabilities(input_ttl: str, output_ttl: Optional[str] = None, double_slip_crossings: bool = True):
    g = Graph()
    g.parse(input_ttl, format="turtle")

    print("Setting the navigabilities between ports.")
    if double_slip_crossings:
        print("All crossings are deemed to be double slip crossings.")
    else:
        print("All crossings are deemed to be diamond crossings.")
    # Get all the ports in the graph
    ports = g.subjects(RDF.type, RSM_TOPOLOGY.Port)  # a generator
    for port in list(ports):
        # Get the connected ports (subjects or objects in the connectedWith property, which is symmetric)
        directly_connected_ports = set(g.objects(port, RSM_TOPOLOGY.connectedWith))
        inverse_connected_ports = set(g.subjects(RSM_TOPOLOGY.connectedWith, port))
        # union of two above sets implies that no connected port is mentioned twice in the resulting list.
        connected_ports_list = list(directly_connected_ports.union(inverse_connected_ports))
        case = len(connected_ports_list)
        if case == 1:
            print(f"**** WARNING: Port {port} has exactly 1 other port connected; should be 0 or >= 2.")
        elif case == 2 or (case == 3 and double_slip_crossings):  # switch, or assumed double-slip crossing
            for other_port in connected_ports_list:
                opposite = get_opposite_port(g, other_port)
                if opposite:
                    azimuth1 = float(g.value(port, RSM_TOPOLOGY.azimuth))
                    azimuth2 = float(g.value(other_port, RSM_TOPOLOGY.azimuth))
                    if possible_navigability(azimuth1, azimuth2):
                        predicate = RSM_TOPOLOGY.navigableTo
                    else:
                        predicate = RSM_TOPOLOGY.nonNavigableTo
                    g.add((port, predicate, opposite))
                    # We assume all navigabilities to be bidirectional by default, and non-navigabilities too.
                    # Also, connectedTo is a symmetric property but the listed connectedWith properties
                    # are expressed one way. Consequently, the navigability the other way round is
                    # expressed below:
                    other_opposite = get_opposite_port(g, port)
                    if other_opposite:
                        g.add((other_port, predicate, other_opposite))
                    else:
                        print(f'**** ERROR: Port {port} has no navigable port on navigable element it belongs to.')
                else:
                    print(f'**** ERROR: Port {other_port} has no opposite port on linear element it belongs to.')
        elif case == 3 and not double_slip_crossings:  # assumption: all crossings are diamond crossings by default
            deviation_angles = []
            for other_port in connected_ports_list:
                opposite = get_opposite_port(g, other_port)
                if opposite:
                    azimuth1 = float(g.value(port, RSM_TOPOLOGY.azimuth))
                    azimuth2 = float(g.value(other_port, RSM_TOPOLOGY.azimuth))
                    deviation_angles += [abs(deviation_angle(azimuth1, azimuth2))]
                else:
                    deviation_angles += [180]
                    print(f'**** ERROR: no opposite port to {other_port} on same linear element')
                # Determine which other_port corresponds to the smallest deviation angle.
                # Navigability will only be possible with its opposite
            smallest_deviation_index = deviation_angles.index(min(deviation_angles))
            smallest_deviation_angle = deviation_angles[smallest_deviation_index]
            for index, other_port in enumerate(connected_ports_list):
                opposite = get_opposite_port(g, other_port)
                other_opposite = get_opposite_port(g, port)
                if index == smallest_deviation_index and smallest_deviation_angle < 30:
                    predicate = RSM_TOPOLOGY.navigableTo
                else:
                    predicate = RSM_TOPOLOGY.nonNavigableTo
                g.add((port, predicate, opposite))
                g.add((other_port, predicate, other_opposite))
        elif case == 0:  # dead-end
            pass
        else:
            raise ValueError(f"Unexpected case: {case} ports connected to port {port}")

    # Output
    if output_ttl:
        g.serialize(destination=output_ttl, format='turtle')
        print(f"Navigabilities were determined. All data saved to {output_ttl}.")
    else:
        print(g.serialize(format='turtle'))
