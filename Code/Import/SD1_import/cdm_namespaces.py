from enum import Enum

from rdflib import Namespace, URIRef
from rdflib.term import _is_valid_uri

from auxiliary import replace_strings

# CDM members

RSM_TOPOLOGY_NAMESPACE = Namespace('http://cdm.ovh/rsm/topology/topology#')

# Other ontologies used by CDM

UNIT_REPRESENTATION = Enum('ucum', 'qudt', 'none')
QUDT_NAMESPACE = Namespace('http://qudt.org/schema/qudt/')
UNIT_NAMESPACE = Namespace('http://qudt.org/vocab/unit/')

# URI management: dictionary of reserved characters in URIs and their ASCII hexadecimal equivalents.
# Only those reserved characters that are currently found in SD1 identifiers are listed.

URI_RESERVED_CHARACTERS = {'[': '%5B', ']': '%5D', '(': '%28', ')': '%29', '>': '%3F'}


def create_uri(uri_value: str, uri_namespace: str) -> URIRef:
    """Creates a URIRef from a SD1 identifier."""
    uri_value = replace_strings(uri_value, URI_RESERVED_CHARACTERS)
    if not _is_valid_uri(uri_value):
        raise ValueError(f"Invalid URI: {uri_value}")
    return URIRef(uri_value, uri_namespace)


def extract_identifier(uri: URIRef) -> str:
    """Gets the SD1 identifier from the URIRef."""
    return replace_strings(str(uri).split('/')[-1], URI_RESERVED_CHARACTERS, reverse_mapping=True)
