from typing import Optional

from rdflib import Graph

FILE_SAVE_MSG = "All data saved to {}"


def load_graph(input_ttl: str) -> Graph:
    graph = Graph()
    graph.parse(input_ttl, format="turtle")
    return graph


def save_graph(graph: Graph, output_ttl: Optional[str]):
    if output_ttl:
        graph.serialize(destination=output_ttl, format='turtle')
        print(FILE_SAVE_MSG.format(output_ttl))
    else:
        print(graph.serialize(format='turtle'))
