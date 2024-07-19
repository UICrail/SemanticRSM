from rdflib import Graph


class SubGraph:
    def __init__(self, graph: Graph):
        self._graph = graph

    def add_triple(self, subj, predicate, obj) -> None:
        self._graph.add((subj, predicate, obj))
