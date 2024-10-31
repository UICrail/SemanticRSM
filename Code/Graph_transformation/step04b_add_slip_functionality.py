# This module will take into account the "slip crossing" or "slip switch" functionality that can be found in
# the provided GeoJSON file as an annotation to artificial linear elements.
# These artefacts are produced in the course of the drawIO-to-GeoJSON conversion (see drawIO_import folder).
# The effect of the module is to
# 1 - add navigabilities corresponding to the slip switch function;
# 2 - remove the artificial linear elements used to express this function.
from rdflib import Literal, Graph
from rdflib.namespace import RDF, RDFS

from Import.drawIO_import.drawIO_XML_to_OSMjson import SLIP_SWITCH_KEY
from Namespaces import GEOSPARQL, RSM_TOPOLOGY, RSM_GEOSPARQL_ADAPTER
from Graph_transformation.graph_file_handing import load_graph, save_graph
from Graph_transformation.geometry_stuff import find_nearest_linear_elements, wkt_point_to_lon_lat, find_nearest_ports
from Graph_transformation.step04_add_port_properties import get_opposite_port


def add_slip_functionality(input_ttl, output_ttl):
    # Load graph
    graph = load_graph(input_ttl)
    print(_add_slip_navigabilities(graph))
    print(_remove_artefacts(graph))
    save_graph(graph, output_ttl)


def _add_slip_navigabilities(graph: Graph) -> str:
    """
    slip switches are encoded, in the graph, as individuals of type LinearElement annotated with rdfs:comment "slip switch".
    Create a list of these individuals and extract the coordinates of their ports (property asWKT).
    Create another list with the genuine LinearElements, i.e. those without the comment rdfs:comment "slip switch".
    For each port of each slip switch, find the linear element that is closest, using the function find_nearest_linear_elements(coords, graph, count: int = 2),
    and then the closest port of this linear element.
    :param graph: the RDF graph to be processed, which already includes ports and usual navigabilities.
    :return: a message that tells how many slip switches were generated, and between which linear element pairs.
    """

    # Lists to hold slip switches and genuine LinearElements
    slip_switches = []
    genuine_elements = []

    # Find and categorize LinearElements
    for subj, _, _ in graph.triples((None, RDF.type, RSM_TOPOLOGY.LinearElement)):
        if (subj, RDFS.comment, Literal(SLIP_SWITCH_KEY)) in graph:
            slip_switches.append(subj)
        else:
            genuine_elements.append(subj)

    slip_switch_count = 0
    slip_switch_pairs = []

    # Process each slip switch
    for slip_switch in slip_switches:
        # Extract coordinates of the ports (property asWKT)
        slip_switch_port_points = [triple[2] for hasPort_triple in
                                   graph.triples((slip_switch, RSM_TOPOLOGY.hasPort, None))
                                   for triple in graph.triples((hasPort_triple[2], GEOSPARQL.asWKT, None))]
        slip_switch_port_coords = list(map(wkt_point_to_lon_lat, map(str, slip_switch_port_points)))

        # Find the nearest linear elements for each coordinate
        nearest_ports = []
        for slip_switch_port_coord in slip_switch_port_coords:
            # here, the nearest element is the slip switch element itself, so we take the second nearest
            nearest_element = list(find_nearest_linear_elements(slip_switch_port_coord, graph, count=2).keys())[1]
            nearest_ports.append(list(find_nearest_ports(slip_switch_port_coord, graph, nearest_element).keys())[0])

        # create the 2 navigabilities resulting from the slip switch
        predicate = RSM_TOPOLOGY.navigableTo
        graph.add((nearest_ports[0], predicate, get_opposite_port(graph, nearest_ports[1])))
        graph.add((nearest_ports[1], predicate, get_opposite_port(graph, nearest_ports[0])))

    return f"Generated {slip_switch_count} slip switches between the following linear element pairs: {slip_switch_pairs}"


def _remove_artefacts(graph: Graph) -> str:
    """
    Removes all individuals (of class LinearElement) that are annotated with "slip switch".
    Removes all property instances where such individuals are subjects or objects.
    :return: message telling how many artefacts of what type (class or property) were removed
    """

    individuals_removed = 0

    individuals_to_remove = []

    classes_to_inspect = [RSM_TOPOLOGY.LinearElement, RSM_TOPOLOGY.Port, RSM_GEOSPARQL_ADAPTER.Geometry]

    for class_to_inspect in classes_to_inspect:
        for subj, pred, obj in graph.triples((None, RDF.type, class_to_inspect)):
            if (subj, RDFS.comment, Literal(SLIP_SWITCH_KEY)) in graph:
                individuals_to_remove.append(subj)

    for individual in individuals_to_remove:
        individuals_removed += 1
        graph.remove((individual, None, None))  # remove all properties where individual is a subject
        graph.remove((None, None, individual))  # remove all properties where individual is an object

    return f"Removed {individuals_removed} individuals (artefacts: slip switches)"
