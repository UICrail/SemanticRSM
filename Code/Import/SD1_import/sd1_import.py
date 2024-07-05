import xml.etree.ElementTree as Et

import rdflib
from rdflib import Namespace
import xmltodict

from cdm_namespaces import RSM_TOPOLOGY_NAMESPACE, QUDT_NAMESPACE, UNIT_NAMESPACE
from Source_data.data_folders import data_root
from topology_import import TopologyGraph

SD1_NAMESPACE = Namespace("http://example.org/sd1/")


def source_xml_file_to_dict(path: str) -> dict:
    # Et.register_namespace(prefix = "", uri=SD1_NAMESPACE)
    xml_data = Et.parse(path).getroot()
    xml_string = Et.tostring(xml_data, encoding="utf-8", method="xml")  # needed to avoid invalid token error
    sd1dict = xmltodict.parse(xml_string)
    return sd1dict


def import_sd1_data(infrastructure_path: str):
    sd1_infra_dict = source_xml_file_to_dict(infrastructure_path)
    trackedge_dict = sd1_infra_dict['ns0:infrastructure']['ns0:topoAreas']['ns0:topoArea']['ns0:trackEdges']
    print(trackedge_dict)
    sd1_graph = rdflib.Graph()
    sd1_graph.bind('scheibenberg', SD1_NAMESPACE)
    sd1_graph.bind('qudt', QUDT_NAMESPACE)
    sd1_graph.bind('rsm', RSM_TOPOLOGY_NAMESPACE)
    sd1_graph.bind('unit', UNIT_NAMESPACE)

    # RSM import statement; not used
    # sd1_graph.add((URIRef(SD1_NAMESPACE), OWL.imports, URIRef(RSM_TOPOLOGY_NAMESPACE)))
    topology_graph = TopologyGraph(sd1_graph)
    for trackedge in trackedge_dict['ns0:trackEdge']:
        sd1id = trackedge['@id']
        length = trackedge['@length']
        unit_repr = 'none'
        topology_graph.add_trackedge_as_linearelement(sd1id, length, SD1_NAMESPACE, unit_repr)
    sd1_graph.print()


if __name__ == '__main__':
    infra_path = data_root + "/scheibenberg/infra_v0.4.2.xml"
    import_sd1_data(infra_path)
