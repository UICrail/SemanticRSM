import xml.etree.ElementTree as Et
from collections import Counter

import xmltodict
from rdflib import Graph

from Export.export_ifcAlignment_to_kml import alignment_to_kml
# from Export.export_ifcAlignment_to_kml import alignment_to_kml
# from Export.export_wkt_to_kml import wkt_to_kml
from Import.SD1_import.cdm_namespaces import SD1_NAMESPACE, IFC_ADAPTER_NAMESPACE
from Import.SD1_import.sd1_alignment_import import AlignmentGraph
from Source_data.data_folders import data_root
from cdm_namespaces import RSM_TOPOLOGY_NAMESPACE, QUDT_NAMESPACE, UNIT_NAMESPACE, GEOSPARQL_NAMESPACE, IFC_NAMESPACE
from sd1_topology_import import TopologyGraph


def create_bindings(a_graph: Graph):
    a_graph.bind('qudt', QUDT_NAMESPACE)
    a_graph.bind('rsm', RSM_TOPOLOGY_NAMESPACE)
    a_graph.bind('unit', UNIT_NAMESPACE)
    a_graph.bind('geosparql', GEOSPARQL_NAMESPACE)
    a_graph.bind('ifc', IFC_NAMESPACE)
    a_graph.bind('ifc_adapter', IFC_ADAPTER_NAMESPACE)
    a_graph.bind('', SD1_NAMESPACE)


def get_infra_dict_from_xml(path: str) -> dict:
    # Et.register_namespace(prefix = "", uri=SD1_NAMESPACE)
    xml_data = Et.parse(path).getroot()
    xml_string = Et.tostring(xml_data, encoding="utf-8", method="xml")  # needed to avoid invalid token error
    infra_dict = xmltodict.parse(xml_string)['ns0:infrastructure']
    return infra_dict


def get_map_dict_from_xml(path: str) -> dict:
    xml_data = Et.parse(path).getroot()
    xml_string = Et.tostring(xml_data, encoding="utf-8", method="xml")  # needed to avoid invalid token error
    map_dict = xmltodict.parse(xml_string)['ns0:mapMgmt']['ns0:mapAreas']['ns0:mapArea']
    return map_dict


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


def get_horizontal_alignment(_infra_dict: dict) -> list:
    return _infra_dict['ns0:geometryAreas']['ns0:geometryArea']['ns0:trackEdgeGeometries']['ns0:trackEdgeGeometry']


def get_trackedges_from_link(infra_dict: dict, link_id: str) -> (str, int, str, int):
    """returns track edge identifiers and position on trackedges (0 is startOfX = 'true')"""
    links_dict = get_trackedge_link_dict(infra_dict)
    link_info = links_dict[link_id]
    position_flags = {'true': 0, 'false': 1}
    teA = link_info['@trackEdgeA']
    position_on_a = position_flags[link_info['@startOfA']]
    teB = link_info['@trackEdgeB']
    position_on_b = position_flags[link_info['@startOfB']]
    return teA, position_on_a, teB, position_on_b


def generate_linear_elements_from_track_edges(infra_dict: dict, topology_graph: TopologyGraph):
    trackedges = get_trackedges(infra_dict)
    for trackedge in trackedges:
        sd1_id = trackedge['@id']
        length = trackedge['@trackEdgeLength']  ## changed attribute name in 1.0
        unit_repr = 'qudt'
        topology_graph.add_trackedge_as_linearelement(sd1_id, length, SD1_NAMESPACE, unit_repr)
    topology_graph.create_ports()


def generate_connections_from_track_edge_links(infra_dict: dict, topology_graph: TopologyGraph):
    trackedge_links = get_trackedge_links(infra_dict)
    for trackedge_link in trackedge_links:
        trackedge_a = trackedge_link['@trackEdgeA']
        trackedge_b = trackedge_link['@trackEdgeB']
        position_on_a = 0 if trackedge_link['@startOfA'] == "true" else 1
        position_on_b = 0 if trackedge_link['@startOfB'] == "true" else 1
        topology_graph.add_connection(trackedge_a, position_on_a, trackedge_b, position_on_b, SD1_NAMESPACE)


def generate_navigabilities_at_simple_points(infra_dict: dict, topology_graph: TopologyGraph):
    """in the SD1 model, navigabilities are documented, inter alia, by simple points associated with
    two track edges links (left and right, for the through and the diverted track).
    In the sample file (Scheibenberg), there are no crossings nor slip crossings."""
    simple_point_dict = get_simple_points(infra_dict)
    for simple_point in simple_point_dict:
        # each simple point will refer to 2 track edge links, hence 4 track edges,
        # two of which will be identical, thus designating the incoming track.
        # the other two are the "left" and "right" outgoing tracks, that we do not further differentiate.
        teA, startOfA_int, teB, startOfB_int = get_trackedges_from_link(infra_dict, simple_point['@pointLeft'])
        teC, startOfC_int, teD, startOfD_int = get_trackedges_from_link(infra_dict, simple_point['@pointRight'])
        te_list = [(teA, startOfA_int), (teB, startOfB_int), (teC, startOfC_int), (teD, startOfD_int)]
        # find the incoming track edge (the one that occurs in both links) by using Counter()
        te_dict = Counter(te_list)
        topology_graph.set_navigabilities_at_simplePoint(te_dict, SD1_NAMESPACE)


#######################################################################################################################
# Main routine
#######################################################################################################################


def import_sd1_infra_data(infrastructure_path: str, map_path: str):
    sd1_infra_dict = get_infra_dict_from_xml(infrastructure_path)
    sd1_map_dict = get_map_dict_from_xml(map_path)

    # RSM import statement; not used
    # sd1_graph.add((URIRef(SD1_NAMESPACE), OWL.imports, URIRef(RSM_TOPOLOGY_NAMESPACE)))

    # TODO: grid reference system should be in the signature too. For the time being, we assume EPSG:25833 to be always valid
    # TODO: the above TODO is no longer correct, EPSG:25833 is irrelevant

    topology_graph = TopologyGraph(sd1_graph)
    generate_linear_elements_from_track_edges(sd1_infra_dict, topology_graph)
    generate_connections_from_track_edge_links(sd1_infra_dict, topology_graph)
    generate_navigabilities_at_simple_points(sd1_infra_dict, topology_graph)

    alignment_graph = AlignmentGraph(sd1_graph, sd1_infra_dict, sd1_map_dict)
    alignment_graph.get_context_info()
    alignment_graph.generate_alignments()


if __name__ == '__main__':
    sd1_graph = Graph()
    create_bindings(sd1_graph)
    infra_path = data_root + "/Scheibenberg-1.0-MBD-0.3/infra_v1.0.xml"
    map_path = data_root + "/Scheibenberg-1.0-MBD-0.3/map_v1.0.xml"
    # SD1 seems to use EPSG:31468 (a Gauss-Krüger projection, based on Bessel 1841 ellipsoid)
    # at version 1.0, they stipulate EPSG 31493
    import_sd1_infra_data(infra_path, map_path)
    sd1_graph.serialize('scheibenberg-1.0.ttl')

#    wkt_to_kml('scheibenberg-1.0.ttl', 'scheibenberg_from_wkt.kml')
    alignment_to_kml('scheibenberg-1.0.ttl', 'scheibenberg_alignment_export_from_CDM_IFC.kml', 31468)

