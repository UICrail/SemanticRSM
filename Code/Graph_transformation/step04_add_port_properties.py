from typing import Optional

from rdflib import Graph
from rdflib.namespace import RDF
from rdflib.term import Node

from Code.Namespaces import *
from Graph_transformation.geometry_stuff import deviation_angle, possible_navigability, \
    NAVIGABILITY_ANGULAR_THRESHOLD
from Graph_transformation.graph_file_handing import load_graph, save_graph

DIRECT_CONNECTION_WARNING_THRESHOLD = 1
DOUBLE_SLIP_CROSSINGS_THRESHOLD = 3
NON_NAVIGABLE_AZIMUTH = 180


def get_ports(graph: Graph) -> list[Node]:
    ports = list(graph.subjects(RDF.type, RSM_TOPOLOGY.Port))  # a generator
    _print_ports_count(ports)
    return ports


def _print_ports_count(ports):
    num_ports = len(ports)
    plural = '' if num_ports == 1 else 's'
    display_count = 'no' if num_ports == 0 else num_ports
    print(f"    {display_count} port{plural} found")


def connect_matching_ports(graph: Graph, ports):
    """
    Connects ports, basing one geometric coincidence.
    :param graph:
    :param ports:
    :return: number of connections made
    """
    connections_count = 0
    for index, port1 in enumerate(ports[:-2]):
        coordinates1 = graph.value(port1, GEOSPARQL.asWKT)
        for port2 in ports[index + 1:]:
            coordinates2 = graph.value(port2, GEOSPARQL.asWKT)
            if coordinates1 == coordinates2:
                graph.add((port1, RSM_TOPOLOGY.connectedWith, port2))
                connections_count += 1
    return connections_count


def set_port_connections(input_ttl: str, output_ttl: Optional[str] = None):
    """
    Yields a new file, with connectedWith properties added.
    :param input_ttl: original RDF file describing the network
    :param output_ttl: new file, with connection properties added
    :return: None
    """
    graph = load_graph(input_ttl)

    print("Setting the connections between ports")

    # Get all the ports in the graph
    ports = get_ports(graph)

    # Iterate over each port
    connections_count = connect_matching_ports(graph, ports)
    print(f"    {connections_count} ports connected")

    # Output
    save_graph(graph, output_ttl=output_ttl)


def get_opposite_port(graph: Graph, port: Node) -> Node | None:
    """
    Looks for the opposite port 0n a linear element.
    If the given port is not a linear element, returns None (and issues a warning).
    :param graph the RDF graph
    :param port a port node in the graph that is supposed to belong to a single linear element
    :returns the opposite port, or None if the element is not a Linear Element
    """
    elements = list(graph.objects(port, RSM_TOPOLOGY.onElement))  # only one element is expected; better check:
    assert len(elements) == 1, "ERROR: port {} belongs to more than one element, namely {} ".format(port,
                                                                                                    elements)
    element = elements[0]
    if graph.value(element, RDF.type) == RSM_TOPOLOGY.LinearElement:
        other_ports = [x for x in graph.subjects(RSM_TOPOLOGY.onElement, element) if x != port]
        return other_ports[0] if other_ports else None
    else:
        print(f"**** WARNING: looking for an opposite port on non-linear element {element}")


def set_navigabilities(input_ttl: str, output_ttl: Optional[str] = None, double_slip_crossings: bool = False):
    graph = load_graph(input_ttl)
    print("Setting the navigabilities between ports.")
    print_crossing_information(double_slip_crossings)

    ports = list(graph.subjects(RDF.type, RSM_TOPOLOGY.Port))  # Convert generator to list
    for port in ports:
        connected_ports, connected_ports_list = get_connected_ports(graph, port)
        handle_port_navigability(graph, port, connected_ports_list, double_slip_crossings)

    save_graph(graph, output_ttl=output_ttl)


def print_crossing_information(double_slip_crossings: bool):
    if double_slip_crossings:
        print("All crossings are deemed to be double slip crossings.")
    else:
        print("All crossings are deemed to be diamond crossings, by default. Additional navigabilities may result, depending on the source.")


def get_connected_ports(graph: Graph, port: Node):
    directly_connected_ports = set(graph.objects(port, RSM_TOPOLOGY.connectedWith))
    inverse_connected_ports = set(graph.subjects(RSM_TOPOLOGY.connectedWith, port))
    connected_ports_list = list(directly_connected_ports.union(inverse_connected_ports))
    return directly_connected_ports, connected_ports_list


def handle_port_navigability(graph: Graph, port: Node, connected_ports_list: list, double_slip_crossings: bool):
    case = len(connected_ports_list)
    if case == DIRECT_CONNECTION_WARNING_THRESHOLD:
        print(f"**** WARNING: Port {port} has exactly 1 other port connected; should be 0 or >= 2.")
    elif case == DOUBLE_SLIP_CROSSINGS_THRESHOLD - 1 or (
            case == DOUBLE_SLIP_CROSSINGS_THRESHOLD and double_slip_crossings):
        process_double_slip_crossing(graph, port, connected_ports_list)
    elif case == DOUBLE_SLIP_CROSSINGS_THRESHOLD and not double_slip_crossings:
        process_diamond_crossing(graph, port, connected_ports_list)
    elif case == 0:  # dead-end
        pass
    else:
        print(f"Unexpected case: {case} ports connected to port {port}")


def process_double_slip_crossing(graph: Graph, port: Node, connected_ports_list: list):
    for other_port in connected_ports_list:
        opposite = get_opposite_port(graph, other_port)
        if opposite:
            azimuth1 = float(graph.value(port, RSM_TOPOLOGY.azimuth))
            azimuth2 = float(graph.value(other_port, RSM_TOPOLOGY.azimuth))
            if possible_navigability(azimuth1, azimuth2):
                predicate = RSM_TOPOLOGY.navigableTo
            else:
                predicate = RSM_TOPOLOGY.nonNavigableTo
            graph.add((port, predicate, opposite))
            other_opposite = get_opposite_port(graph, port)
            if other_opposite:
                graph.add((other_port, predicate, other_opposite))
            else:
                print(f'**** ERROR: Port {port} has no navigable port on navigable element it belongs to.')
        else:
            print(f'**** ERROR: Port {other_port} has no opposite port on linear element it belongs to.')


def process_diamond_crossing(graph: Graph, port: Node, connected_ports_list: list):
    deviation_angles = []
    for other_port in connected_ports_list:
        opposite = get_opposite_port(graph, other_port)
        if opposite:
            azimuth1 = float(graph.value(port, RSM_TOPOLOGY.azimuth))
            azimuth2 = float(graph.value(other_port, RSM_TOPOLOGY.azimuth))
            deviation_angles.append(abs(deviation_angle(azimuth1, azimuth2)))
        else:
            deviation_angles.append(NON_NAVIGABLE_AZIMUTH)
            print(f'**** ERROR: no opposite port to {other_port} on same linear element')

    smallest_deviation_index = deviation_angles.index(min(deviation_angles))
    smallest_deviation_angle = deviation_angles[smallest_deviation_index]
    for index, other_port in enumerate(connected_ports_list):
        opposite = get_opposite_port(graph, other_port)
        other_opposite = get_opposite_port(graph, port)
        if index == smallest_deviation_index and smallest_deviation_angle < NAVIGABILITY_ANGULAR_THRESHOLD:
            predicate = RSM_TOPOLOGY.navigableTo
        else:
            predicate = RSM_TOPOLOGY.nonNavigableTo
        graph.add((port, predicate, opposite))
        graph.add((other_port, predicate, other_opposite))
