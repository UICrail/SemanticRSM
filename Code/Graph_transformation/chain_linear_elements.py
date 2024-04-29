from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, RDF
from shapely import LineString
from shapely.geometry import Point
from shapely.wkt import loads, dumps
from shapely.ops import linemerge
from collections import Counter
from typing import Dict, List, Optional, Set

GEO = Namespace("http://www.opengis.net/ont/geosparql#")
RSM = Namespace("http://www.example.org/rsm#")


def create_nodes(g: Graph) -> Dict[str, List[URIRef]]:
    """
    Creates a dictionary:
    key = WKT POINTs at extremities of linear elements
    values = URIs of those linear elements, based on the provided RDF graph.
    """
    nodes: Dict[str, List[URIRef]] = {}
    for s, _, o in g.triples((None, GEO.asWKT, None)):
        if (s, RDF.type, RSM.LinearElement) in g:
            geom = loads(str(o))
            if isinstance(geom, Point):
                print('WARNING: a point was found in the topology.ttl graph, where only linestrings are expected.')
            else:
                start_point_wkt = dumps(Point(geom.coords[0]))
                end_point_wkt = dumps(Point(geom.coords[-1]))

                if start_point_wkt in nodes:
                    nodes[start_point_wkt].append(s)
                else:
                    nodes[start_point_wkt] = [s]

                if start_point_wkt != end_point_wkt:
                    if end_point_wkt in nodes:
                        nodes[end_point_wkt].append(s)
                    else:
                        nodes[end_point_wkt] = [s]

    return nodes


def report_degrees(nodes: Dict[str, List[URIRef]]) -> None:
    """
    Reports the number of nodes for each degree (number of related linear elements).
    """
    degrees = Counter(len(v) for v in nodes.values())
    for degree, count in degrees.items():
        print(f"Nodes with degree {degree}: {count}")


def perform_chaining(g: Graph, nodes_degree_2: Dict[str, List[URIRef]]) -> Graph:
    """
    Performs chaining on linear elements that meet at nodes with degree 2 and updates references.
    """
    # Prepare a set for elements to be removed and a dict for updating node references
    elements_to_remove: Set[URIRef] = set()
    nodes_updates: Dict[str, List[URIRef]] = {}

    for node_wkt, elements in nodes_degree_2.items():
        geom_x = loads(str(g.value(elements[0], GEO.asWKT)))
        geom_y = loads(str(g.value(elements[1], GEO.asWKT)))

        # Chain the geometries
        geom_z = linemerge([geom_x, geom_y])

        if geom_z.is_valid and isinstance(geom_z, LineString):
            uri_z = URIRef(f"{str(elements[0])}_chained_with_{str(elements[1])}")

            # Add the new chained element Z
            g.add((uri_z, RDF.type, RSM.LinearElement))
            g.add((uri_z, GEO.asWKT, Literal(dumps(geom_z), datatype=GEO.wktLiteral)))

            # Mark X and Y for removal
            elements_to_remove.update(elements)

            # Prepare updates for nodes referring to X or Y
            for e in elements:
                for n_wkt, e_list in nodes_degree_2.items():
                    if e in e_list:
                        if n_wkt in nodes_updates:
                            nodes_updates[n_wkt].append(uri_z)
                        else:
                            nodes_updates[n_wkt] = [uri_z for _ in e_list]

    # Remove the marked original elements X and Y from the graph
    for e in elements_to_remove:
        g.remove((e, None, None))

    # Update nodes_degree_2 with Z replacing X and Y
    for n_wkt, new_elements in nodes_updates.items():
        nodes_degree_2[n_wkt] = new_elements

    # Remove nodes that were only associated with removed elements
    nodes_degree_2 = {k: v for k, v in nodes_degree_2.items() if not set(v).issubset(elements_to_remove)}

    return g


def chain_linear_elements(input_ttl: str, output_ttl: Optional[str] = None) -> None:
    """
    Chains linear elements based on nodes with degree 2. Updates an RDF graph accordingly and
    optionally saves the updated graph to a Turtle file.
    """
    # Create the RDF graph by parsing the input TTL file
    g = Graph()
    g.parse(input_ttl, format='turtle')

    # Invoke create_nodes with the RDF graph to generate the mapping of nodes to linear elements
    nodes = create_nodes(g)

    # Report the number of nodes per degree
    report_degrees(nodes)

    # Update the nodes dictionary to keep only nodes with degree 2
    nodes_degree_2 = {k: v for k, v in nodes.items() if len(v) == 2}

    print(f'Performing the chaining on {len(nodes_degree_2)} nodes of degree 2:')
    g_chained = perform_chaining(g, nodes_degree_2)

    if g_chained and output_ttl:
        print(f"Chained RDF graph will be saved to: {output_ttl}")
        g_chained.serialize(destination=output_ttl, format='turtle')
    elif output_ttl:
        print("No chaining performed. Original graph will be saved.")
        g.serialize(destination=output_ttl, format='turtle')


if __name__ == "__main__":
    chain_linear_elements("/Users/airymagnien/PycharmProjects/SemanticRSM/Intermediate_files/osm_railways_split.ttl",
                          "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/osm_railways_chained.ttl")
