import rdflib
from rdflib import BNode, URIRef, RDF, XSD, Literal
from rdflib.term import Node

from auxiliary import millimeters_to_meters
from cdm_namespaces import QUDT_NAMESPACE, UNIT_NAMESPACE, RSM_TOPOLOGY_NAMESPACE, UNIT_REPRESENTATION, create_uri


class TopologyGraph:

    def __init__(self, graph: rdflib.Graph):
        self._graph = graph
        self.express_length_and_unit = {
            'ucum': self.add_ucum_length_and_unit,
            'qudt': self.add_qudt_length_and_unit,
            'none': self.add_length_without_unit
        }

    def add_triple(self, subj: Node, predicate: Node, obj: Node):
        self._graph.add((subj, predicate, obj))

    def add_qudt_value_node(self, some_value: str, subject: URIRef, datatype=XSD.decimal):
        value_node = BNode()
        self.add_triple(value_node, RDF.type, QUDT_NAMESPACE.QuantityValue)
        self.add_triple(value_node, QUDT_NAMESPACE.numericValue, Literal(some_value, datatype=datatype))
        self.add_triple(value_node, QUDT_NAMESPACE.unit, UNIT_NAMESPACE.M)
        self.add_triple(subject, RSM_TOPOLOGY_NAMESPACE.hasNominalMetricLength, value_node)

    def add_qudt_length_and_unit(self, length: str, subject: URIRef):
        self.add_qudt_value_node(length, subject)

    def add_ucum_length_and_unit(self, length: str, subject: URIRef):
        self.add_triple(subject, RSM_TOPOLOGY_NAMESPACE.hasNominalMetricLength,
                        Literal(length + ' m', datatype=XSD.string))

    def add_length_without_unit(self, length: str, subject: URIRef):
        self.add_triple(subject, RSM_TOPOLOGY_NAMESPACE.hasNominalMetricLength, Literal(length, datatype=XSD.decimal))

    def add_trackedge_as_linearelement(self, sd1id: str, length: str, namespace: str,
                                       unit_repr: UNIT_REPRESENTATION = 'none'):
        subject = create_uri(sd1id, namespace)
        length_in_meter = millimeters_to_meters(length)
        self.add_triple(subject, RDF.type, RSM_TOPOLOGY_NAMESPACE.LinearElement)
        self.express_length_and_unit[unit_repr](length_in_meter, subject)

    def create_ports(self):
        """Create ports 0 and 1 for each linear element"""
        for linear_element in self._graph.subjects(RDF.type, RSM_TOPOLOGY_NAMESPACE.LinearElement):
            port_0 = linear_element + '_port_0'
            port_1 = linear_element + '_port_1'
            self.add_triple(URIRef(port_0), RDF.type, RSM_TOPOLOGY_NAMESPACE.Port)
            self.add_triple(URIRef(port_1), RDF.type, RSM_TOPOLOGY_NAMESPACE.Port)
            self.add_triple(linear_element, RSM_TOPOLOGY_NAMESPACE.hasPort, port_0)
            self.add_triple(linear_element, RSM_TOPOLOGY_NAMESPACE.hasPort, port_1)

    def add_connection(self, trackedge_a: str, position_on_a: int, trackedge_b: str, position_on_b: int, _namespace: str):
        port_a = create_uri(trackedge_a, _namespace) + '_port_' + str(position_on_a)
        port_b = create_uri(trackedge_b, _namespace) + '_port_' + str(position_on_b)
        self.add_triple(port_a, RSM_TOPOLOGY_NAMESPACE.connectedWith, port_b)

    def add_connexity(self):
        """called trackEdgeLink in SD1 model"""
        pass
