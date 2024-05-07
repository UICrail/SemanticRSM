from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
from shapely import LineString
from shapely.geometry import Point
from shapely.wkt import loads, dumps
from shapely.ops import linemerge
from collections import Counter
from typing import Dict, List, Optional
from Code.Namespaces import *
import copy

# string used for expressing the chaining of elements in the chained element URI
CHAINED_WITH = '-'


def create_nodes(g: Graph) -> Dict[str, List[URIRef]]:
    """
    Creates a dictionary:
    key = WKT POINT shared by extremities of linear elements
    values = URIs of those linear elements, based on the provided RDF graph.
    """
    nodes: Dict[str, List[URIRef]] = {}
    for s, _, o in g.triples((None, GSP.asWKT, None)):
        if (s, RDF.type, RSM_TOPOLOGY.LinearElement) in g:
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


def report_degrees(nodes: dict[str, list[URIRef]]) -> None:
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
    elements_to_remove: set[URIRef] = set()
    unprocessed_nodes = copy.deepcopy(nodes_degree_2)
    processed_nodes_counter = 0

    for node_wkt, elements in nodes_degree_2.items():
        geom_x = loads(str(g.value(elements[0], GSP.asWKT)))
        geom_y = loads(str(g.value(elements[1], GSP.asWKT)))

        # Chain the geometries
        # Here, directed should be set to False (the default argument), otherwise multi-linestrings
        # will result when linestrings start of finish with a common point.
        geom_z = linemerge([geom_x, geom_y], directed=False)
        del unprocessed_nodes[node_wkt]

        if geom_z.is_valid and isinstance(geom_z, LineString):
            processed_nodes_counter += 1
            uri_z = URIRef(f"{str(elements[0])}{CHAINED_WITH}{str(elements[1]).split('#', 1)[1]}")
            # Add the new chained element Z to the graph
            g.add((uri_z, RDF.type, RSM_TOPOLOGY.LinearElement))
            g.add((uri_z, GSP.asWKT, Literal(dumps(geom_z), datatype=GSP.wktLiteral)))

            # Mark X and Y for removal
            elements_to_remove.update(elements)

            # Updates references made to X or Y by nodes not yet processed
            # Note: we are looping through the nodes_degree_2 dict;
            # here, the values in the nodes_degree_2 dict are altered, but not the keys, which is legal.
            for chained_element in elements:
                for n_wkt in unprocessed_nodes:
                    if chained_element in nodes_degree_2[n_wkt]:
                        nodes_degree_2[n_wkt].append(uri_z)
                        nodes_degree_2[n_wkt].remove(chained_element)
        else:
            print(f"WARNING: strange things happening at {node_wkt}: chaining was not successful.")

    # Remove the marked original elements X and Y from the graph
    for chained_element in elements_to_remove:
        g.remove((chained_element, None, None))

    # Update nodes_degree_2 with Z replacing X and Y
    for n_wkt, new_elements in unprocessed_nodes.items():
        nodes_degree_2[n_wkt] = new_elements

    print(f"{processed_nodes_counter} nodes of degree 2 were removed by chaining the surrounding linestrings")

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
