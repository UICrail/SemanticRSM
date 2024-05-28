import copy
from collections import Counter
from typing import Dict, List, Optional

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
from shapely.geometry import Point
from shapely.ops import linemerge
from shapely.wkt import loads, dumps

from Code.Namespaces import *




def find_nodes(g: Graph) -> Dict[str, List[URIRef]]:
    """
    Creates a dictionary:
    key = WKT POINT at extremities of linear elements (called "nodes" in the present context)
    values = URIs of those linear elements, based on the provided RDF graph.
    """
    nodes: dict[str, List[URIRef]] = {}
    for line in g.subjects(RDF.type, RSM_TOPOLOGY.LinearElement):
        for geom in g.objects(line, RSM_GEOSPARQL_ADAPTER.hasNominalGeometry):
            s_wkt = loads(str(next(g.objects(geom, GEOSPARQL.asWKT))))  # Shapely geometry object
            if isinstance(s_wkt, Point):
                print('WARNING: a point was found in the topology.ttl graph, where only linestrings are expected.')
            else:
                start_point_wkt = dumps(Point(s_wkt.coords[0]))
                end_point_wkt = dumps(Point(s_wkt.coords[-1]))
                if start_point_wkt in nodes:
                    nodes[start_point_wkt].append(line)
                else:
                    nodes[start_point_wkt] = [line]
                if end_point_wkt == start_point_wkt:  # equality may happen in the presence of loops.
                    print(f"Loop found : {start_point_wkt} -> {end_point_wkt}")
                else:
                    if end_point_wkt in nodes:
                        nodes[end_point_wkt].append(line)
                    else:
                        nodes[end_point_wkt] = [line]
    return nodes


def report_degrees(nodes: dict[str, list[URIRef]]) -> None:
    """
    Reports the number of nodes for each degree (number of related linear elements).
    """
    degrees = Counter(len(v) for v in nodes.values())
    for degree, count in degrees.items():
        print(f"Nodes with degree {degree}: {count}")
    pass


def chain_URIRefs(*URIRefs: URIRef, chain_symbol: str = '-') -> (URIRef, URIRef):
    """
    Assumes that all URI bases are the same
    :param chain_symbol:
    :param URIRefs:
    :return:
    """
    if len(URIRefs) < 2:
        raise ValueError(f"ERROR: at least two URI references are required. {str(URIRefs)} falls short.")
    else:
        geom_base = URIRefs[0].split('#', 1)[0] + '#geometry_'
        line_base=URIRefs[0].split('#', 1)[0] + '#element_'
        extension = ''
        for uri_ref in URIRefs[0:-1]:
            extension += uri_ref.split('#', 1)[1] + chain_symbol
        extension = extension + URIRefs[-1].split('#',1)[1] if URIRefs[-1] is not None else geom_base
        geom_result = geom_base + extension
        line_result = line_base + extension
        return URIRef(geom_result), URIRef(line_result)


def perform_chaining(g: Graph, nodes_degree_2: Dict[str, List[URIRef]]) -> Graph:
    """
    Performs chaining on linear elements that meet at nodes with degree 2 and updates references.
    """
    # Prepare a set for elements to be removed and a dict for updating node references
    lines_to_remove: set[URIRef] = set()
    geometries_to_remove: set[URIRef] = set()
    unprocessed_nodes = copy.deepcopy(nodes_degree_2)
    processed_nodes_counter = 0

    parse_error_count = 0

    for node_wkt, linear_elements in nodes_degree_2.items():
        x_geom = g.value(linear_elements[0], RSM_GEOSPARQL_ADAPTER.hasNominalGeometry)
        y_geom = g.value(linear_elements[1], RSM_GEOSPARQL_ADAPTER.hasNominalGeometry)
        try:
            x_wkt = loads(str(g.value(x_geom, GEOSPARQL.asWKT)))
            y_wkt = loads(str(g.value(y_geom, GEOSPARQL.asWKT)))
        except Exception:
            print(f'WARNING: could not parse geometries surrounding {node_wkt} for WKT data')
            parse_error_count += 1
            continue

        # Chain the geometries
        # Here, directed should be set to False (the default argument), otherwise multi-linestrings
        # will result when linestrings start of finish with a common point.
        z_wkt = linemerge([x_wkt, y_wkt], directed=False)
        del unprocessed_nodes[node_wkt]

        if z_wkt.is_valid:
            processed_nodes_counter += 1
            geom_uri_z, line_uri_z = chain_URIRefs(x_geom, y_geom)
            # Add the new chained element Z to the graph
            g.add((geom_uri_z, RDF.type, RSM_GEOSPARQL_ADAPTER.Geometry))
            g.add((geom_uri_z, GEOSPARQL.asWKT, Literal(dumps(z_wkt), datatype=GEOSPARQL.wktLiteral)))

            # Add the corresponding linear element
            g.add((line_uri_z, RDF.type, RSM_TOPOLOGY.LinearElement))
            g.add((line_uri_z, RSM_GEOSPARQL_ADAPTER.hasNominalGeometry, geom_uri_z))

            # Mark linear elements and geometries for removal
            lines_to_remove.update(linear_elements)
            geometries_to_remove.update((x_geom, y_geom))

            # Updates references made to X or Y by nodes not yet processed
            # Note: we are looping through the nodes_degree_2 dict;
            # here, the values in the nodes_degree_2 dict are altered, but not the keys, which is legal.
            for chained_element in linear_elements:
                for n_wkt in unprocessed_nodes:
                    if chained_element in nodes_degree_2[n_wkt]:
                        nodes_degree_2[n_wkt].append(geom_uri_z)
                        nodes_degree_2[n_wkt].remove(chained_element)
        else:
            print(f"WARNING: strange things happening at {node_wkt}: chaining was not successful.")

    print(f"WARNING: parsing errors around {parse_error_count} nodes")

    # Remove the marked original elements from the graph
    for line in lines_to_remove:
        g.remove((line, None, None))
    for geom in geometries_to_remove:
        g.remove((geom, None, None))
        g.remove((None, None, geom))

    # Update nodes_degree_2
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
    nodes = find_nodes(g)

    # Report the number of nodes per degree
    report_degrees(nodes)

    # Update the nodes dictionary to keep only nodes with degree 2
    nodes_degree_2 = {k: v for k, v in nodes.items() if len(v) == 2}

    print(
        f'Performing the chaining on {len(nodes_degree_2)} nodes of degree 2 (revealing consecutive linear elements):')
    g_chained = perform_chaining(g, nodes_degree_2)

    if g_chained and output_ttl:
        print(f"Chained RDF graph will be saved to: {output_ttl}")
        g_chained.serialize(destination=output_ttl, format='turtle')
    elif output_ttl:
        print("No chaining performed. Original graph will be saved.")
        g.serialize(destination=output_ttl, format='turtle')
    pass


if __name__ == "__main__":
    chain_linear_elements("/Users/airymagnien/PycharmProjects/SemanticRSM/Intermediate_files/osm_railways_split.ttl",
                          "/Users/airymagnien/PycharmProjects/SemanticRSM/Output_files/osm_railways_chained.ttl")
