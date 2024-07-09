import xml.etree.ElementTree as Et
from collections import Counter

import xmltodict
from rdflib import Graph
from rdflib import Namespace

from Source_data.data_folders import data_root
from cdm_namespaces import RSM_TOPOLOGY_NAMESPACE, QUDT_NAMESPACE, UNIT_NAMESPACE
from sd1_topology_import import TopologyGraph

SD1_NAMESPACE = Namespace("http://example.org/scheibenberg/")


def create_bindings(_sd1_graph: Graph):
    _sd1_graph.bind('qudt', QUDT_NAMESPACE)
    _sd1_graph.bind('rsm', RSM_TOPOLOGY_NAMESPACE)
    _sd1_graph.bind('unit', UNIT_NAMESPACE)
    _sd1_graph.bind('', SD1_NAMESPACE)


def get_infra_dict_from_xml(path: str) -> dict:
    # Et.register_namespace(prefix = "", uri=SD1_NAMESPACE)
    xml_data = Et.parse(path).getroot()
    xml_string = Et.tostring(xml_data, encoding="utf-8", method="xml")  # needed to avoid invalid token error
    infra_dict = xmltodict.parse(xml_string)['ns0:infrastructure']
    return infra_dict


def get_trackedges(infra_dict: dict) -> list:
    return infra_dict['ns0:topoAreas']['ns0:topoArea']['ns0:trackEdges']['ns0:trackEdge']


def get_trackedge_dict(infra_dict: dict) -> dict:
    return {link['@id']: link for link in get_trackedges(infra_dict)}


def get_trackedge_links(_infra_dict: dict) -> list:
    return _infra_dict['ns0:topoAreas']['ns0:topoArea']['ns0:trackEdgeLinks']['ns0:trackEdgeLink']


def get_trackedge_link_dict(infra_dict: dict) -> dict:
    return {link['@id']: link for link in get_trackedge_links(infra_dict)}


def get_simple_points(_infra_dict: dict) -> list:
    return _infra_dict['ns0:functionalAreas']['ns0:functionalArea']['ns0:simplePoints']['ns0:simplePoint']


def get_trackedges_from_link(infra_dict: dict, link: str) -> (str, int, str, int):
    links_dict = get_trackedge_link_dict(infra_dict)
    link_info = links_dict[link]
    start_flags = {True: 0, False: 1}
    teA = link_info['@trackEdgeA']
    start_of_A = start_flags[link_info['@startOfA']]
    teB = link_info['@trackEdgeB']
    start_of_B = start_flags[link_info['@startOfB']]
    return teA, start_of_A, teB, start_of_B


def generate_linear_elements_from_track_edges(_infra_dict: dict, _topology_graph: TopologyGraph):
    trackedges = get_trackedges(_infra_dict)
    for trackedge in trackedges:
        sd1id = trackedge['@id']
        length = trackedge['@length']
        unit_repr = 'qudt'
        _topology_graph.add_trackedge_as_linearelement(sd1id, length, SD1_NAMESPACE, unit_repr)
    _topology_graph.create_ports()


def generate_connections_from_track_edge_links(_infra_dict: dict, _topology_graph: TopologyGraph):
    trackedge_links = get_trackedge_links(_infra_dict)
    for trackedge_link in trackedge_links:
        trackedge_a = trackedge_link['@trackEdgeA']
        trackedge_b = trackedge_link['@trackEdgeB']
        position_on_a = 0 if trackedge_link['@startOfA'] == "true" else 1
        position_on_b = 0 if trackedge_link['@startOfB'] == "true" else 1
        _topology_graph.add_connection(trackedge_a, position_on_a, trackedge_b, position_on_b, SD1_NAMESPACE)


def get_trackedges_from_link(_infra_dict: dict, _link: str) -> (str, int, str, int):
    links_dict = get_trackedge_link_dict(_infra_dict)
    teA = links_dict[_link]['@trackEdgeA']
    startOfA_int = 0 if links_dict[_link]['@startOfA'] else 1
    teB = links_dict[_link]['@trackEdgeB']
    startOfB_int = 0 if links_dict[_link]['@startOfB'] else 1
    return teA, startOfA_int, teB, startOfB_int


def generate_navigabilities_at_simple_points(_infra_dict: dict, _topology_graph: TopologyGraph):
    """in the SD1 model, navigabilities are documented, inter alia, by simple points associated with
    two track edges links (left and right, for the through and the diverted track).
    In the sample file (Scheibenberg), there are no crossings nor slip crossings."""
    simple_point_dict = get_simple_points(_infra_dict)
    for simple_point in simple_point_dict:
        # each simple point will refer to 2 track edge links, hence 4 track edges,
        # two of which will be identical, thus designating the incoming track.
        # the other two are the "left" and "right" outgoing tracks, that we do not further differentiate.
        teA, startOfA_int, teB, startOfB_int = get_trackedges_from_link(_infra_dict, simple_point['@pointLeft'])
        teC, startOfC_int, teD, startOfD_int = get_trackedges_from_link(_infra_dict, simple_point['@pointRight'])
        te_list = [(teA, startOfA_int), (teB, startOfB_int), (teC, startOfC_int), (teD, startOfD_int)]
        # find the incoming track edge (the one that occurs in both links) by using Counter()
        te_dict = Counter(te_list)
        _topology_graph.set_navigabilities_at_simplePoint(te_dict)


#######################################################################################################################
# Main routine
#######################################################################################################################


def import_sd1_infra_data(infrastructure_path: str):
    sd1_infra_dict = get_infra_dict_from_xml(infrastructure_path)

    # RSM import statement; not used
    # sd1_graph.add((URIRef(SD1_NAMESPACE), OWL.imports, URIRef(RSM_TOPOLOGY_NAMESPACE)))

    topology_graph = TopologyGraph(sd1_graph)
    generate_linear_elements_from_track_edges(sd1_infra_dict, topology_graph)
    generate_connections_from_track_edge_links(sd1_infra_dict, topology_graph)
    generate_navigabilities_at_simple_points(sd1_infra_dict, topology_graph)


if __name__ == '__main__':
    sd1_graph = Graph()
    create_bindings(sd1_graph)
    infra_path = data_root + "/scheibenberg/infra_v0.4.2.xml"
    import_sd1_infra_data(infra_path)
    sd1_graph.print()
