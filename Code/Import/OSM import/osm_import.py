from osmread import parse_file, Node, Way
import rdflib
from rdflib.namespace import RDF, OWL, Namespace

# Initialize namespaces
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
MY_NS = Namespace("http://www.example.org/osm#")

# Initialize an RDF graph
g = rdflib.Graph()

# Define the class structure
g.add((MY_NS.Link, RDF.type, OWL.Class))
g.add((MY_NS.Link, RDFS.subClassOf, GEO.Geometry))

# Function to add nodes to the RDF graph, same as before
def add_node(node):
    ...

# Adjusted function to add links between nodes to the RDF graph
def add_link(node_id1, node_id2, node1_coords, node2_coords):
    link_uri = MY_NS[f"link/{node_id1}_to_{node_id2}"]
    g.add((link_uri, RDF.type, MY_NS.Link))
    wkt_line = rdflib.Literal(f"LINESTRING({node1_coords[1]} {node1_coords[0]}, {node2_coords[1]} {node2_coords[0]})", datatype=GEO.wktLiteral)
    g.add((link_uri, GEO.asWKT, wkt_line))

# Store node information for easy lookup
nodes_info = {}

# Adjusted parsing logic
for entity in parse_file('path_to_your_osm_file.osm'):
    if isinstance(entity, Node):
        add_node(entity)
        nodes_info[entity.id] = (entity.lat, entity.lon)
    elif isinstance(entity, Way):
        for i in range(len(entity.nodes) - 1):
            node1_id, node2_id = entity.nodes[i], entity.nodes[i + 1]
            node1_coords, node2_coords = nodes_info[node1_id], nodes_info[node2_id]
            add_link(node1_id, node2_id, node1_coords, node2_coords)

# Serialize the graph to a Turtle file
g.serialize(destination='output_with_links_as_geometry.ttl', format='turtle')
