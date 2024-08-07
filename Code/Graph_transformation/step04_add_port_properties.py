import itertools
from typing import Optional

from rdflib import Graph
from rdflib.namespace import RDF
from rdflib.term import Node

from Code.Namespaces import *


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


def deviation_angle(azimuth_1: float, azimuth_2: float) -> float:
    """
    Deviation angle at the junction between two linear elements.
    :param azimuth_1: of port X of element A at junction
    :param azimuth_2: of port Y of element B at junction
    :return: angle, in degrees, in [-180, 180] interval
    """
    dev = azimuth_1 - (azimuth_2 - 180)
    if dev > 180:
        dev -= 360
    elif dev < -180:
        dev += 360
    return dev


def possible_navigability(azimuth_1: float, azimuth_2: float, small_angle: float = 30) -> bool:
    """
    Determines whether it is possible to navigate between linear elements basing on the azimuths of their connected
    extremities. Azimuths values are provided in degrees, in the range [-180, 180] (this is a pyproj setting).
    "Possibility" is provided when the azimuth difference, modulo 180 degrees, is "small".
    :param azimuth_1:
    :param azimuth_2:
    :param small_angle: 30° by default
    :return: True if navigability is possible, else False
    """
    if abs(deviation_angle(azimuth_1, azimuth_2)) < small_angle:
        return True
    else:
        return False


def get_opposite_port(g: Graph, a_port: Node) -> Node | None:
    """
    Leads from a_port to the other port in the same linear element
    :returns the opposite port, or None if the element is not a Linear Element
    """
    element = list(g.objects(a_port, RSM_TOPOLOGY.onElement))  # only one element is expected; better check
    assert len(element) == 1
    other_port = []
    if g.value(element[0], RDF.type) == RSM_TOPOLOGY.LinearElement:
        other_port = [x for x in g.subjects(RSM_TOPOLOGY.onElement, element[0]) if x != a_port]
    return other_port[0] if other_port else None


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
