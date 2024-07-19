from enum import Enum

from rdflib import Namespace, URIRef
from rdflib.term import _is_valid_uri

from helper_functions import replace_strings

# CDM members

RSM_TOPOLOGY_NAMESPACE = Namespace('http://cdm.ovh/rsm/topology/topology#')

# Other ontologies used by CDM

UNIT_REPRESENTATION = Enum('ucum', 'qudt', 'none')
QUDT_NAMESPACE = Namespace('http://qudt.org/schema/qudt/')
UNIT_NAMESPACE = Namespace('http://qudt.org/vocab/unit/')
GEOSPARQL_NAMESPACE = Namespace('http://www.opengis.net/ont/geosparql')
IFC_NAMESPACE = Namespace('https://w3id.org/ifc/IFC4X3_ADD2#')
IFC_ADAPTER_NAMESPACE = Namespace('https://cdm.ovh/adapters/ifcowl_rsm')

# URI management: dictionary of reserved characters in URIs and their ASCII hexadecimal equivalents.
# Only those reserved characters that are currently found in SD1 identifiers are listed.

URI_RESERVED_CHARACTERS = {'[': '%5B', ']': '%5D', '(': '%28', ')': '%29', '>': '%3F'}


def create_uri(sd1_identifier: str, uri_namespace: str = '') -> URIRef:
    """Creates a URIRef from a SD1 identifier."""
    sd1_identifier = replace_strings(sd1_identifier, URI_RESERVED_CHARACTERS)
    if not _is_valid_uri(sd1_identifier):
        raise ValueError(f"Invalid URI: {sd1_identifier}")
    return URIRef(sd1_identifier, uri_namespace)


def extract_identifier(uri: URIRef) -> str:
    """Gets the SD1 identifier from the URIRef."""
    return replace_strings(str(uri).split('/')[-1], URI_RESERVED_CHARACTERS, reverse_mapping=True)


SD1_NAMESPACE = Namespace("http://example.org/scheibenberg/")
