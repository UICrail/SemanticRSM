import xml.etree.ElementTree as Et

import xmltodict
from rdflib import Graph
from rdflib import Namespace

from Source_data.data_folders import data_root
from cdm_namespaces import RSM_TOPOLOGY_NAMESPACE, QUDT_NAMESPACE, UNIT_NAMESPACE
from sd1_topology_import import TopologyGraph

SD1_NAMESPACE = Namespace("http://example.org/scheibenberg/")


def get_infra_dict_from_xml(path: str) -> dict:
    # Et.register_namespace(prefix = "", uri=SD1_NAMESPACE)
    xml_data = Et.parse(path).getroot()
    xml_string = Et.tostring(xml_data, encoding="utf-8", method="xml")  # needed to avoid invalid token error
    infra_dict = xmltodict.parse(xml_string)['ns0:infrastructure']
    return infra_dict


def create_bindings(_sd1_graph: Graph):
    _sd1_graph.bind('qudt', QUDT_NAMESPACE)
    _sd1_graph.bind('rsm', RSM_TOPOLOGY_NAMESPACE)
    _sd1_graph.bind('unit', UNIT_NAMESPACE)
    _sd1_graph.bind('', SD1_NAMESPACE)


def generate_linear_elements_from_track_edges(_infra_dict: dict, _topology_graph: TopologyGraph):
    trackedge_dict = _infra_dict['ns0:topoAreas']['ns0:topoArea']['ns0:trackEdges']['ns0:trackEdge']
    for trackedge in trackedge_dict:
        sd1id = trackedge['@id']
        length = trackedge['@length']
        unit_repr = 'qudt'
        _topology_graph.add_trackedge_as_linearelement(sd1id, length, SD1_NAMESPACE, unit_repr)
    _topology_graph.create_ports()


def generate_connections_from_track_edge_links(_infra_dict: dict, _topology_graph: TopologyGraph):
    trackedge_link_dict = _infra_dict['ns0:topoAreas']['ns0:topoArea']['ns0:trackEdgeLinks']['ns0:trackEdgeLink']
    for trackedge_link in trackedge_link_dict:
        trackedge_a = trackedge_link['@trackEdgeA']
        trackedge_b = trackedge_link['@trackEdgeB']
        position_on_a = 0 if trackedge_link['@startOfA'] == "true" else 1
        position_on_b = 0 if trackedge_link['@startOfB'] == "true" else 1
        _topology_graph.add_connection(trackedge_a, position_on_a, trackedge_b, position_on_b, SD1_NAMESPACE)


def generate_navigabilities_at_simple_points(_infra_dict: dict, _topology_graph: TopologyGraph):
    simple_point_dict = _infra_dict['ns0:functionalAreas']['ns0:functionalArea']['ns0:simplePoints'][
        'ns0:simplePoint']
    for simple_point in simple_point_dict:
        point_left = simple_point['@pointLeft']
        point_right = simple_point['@pointRight']


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
