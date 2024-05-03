from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
from shapely import LineString
from shapely.geometry import Point
from shapely.wkt import loads, dumps
from shapely.ops import linemerge
from collections import Counter
from typing import Dict, List, Optional, Set
from Code.Namespaces import *


def add_ports(graph: Graph):
    """
    Assume that graph only contains linear elements and their geometry (linestrings)
    :param graph: modified in place
    :return:
    """
    #TODO: to be completed
    for s, _, _ in graph.triples((None, RDF.type, RSM_TOPOLOGY.LinearElement)):
        if (s, GEO.asWKT, None) in graph:
            ls = LineString([(s, GEO.asWKT, None)])

