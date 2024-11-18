import os

from lxml import etree
from rdflib import RDF, BNode, Literal, URIRef, XSD, Graph

from Namespaces import RSM_TOPOLOGY, RSM_GEOSPARQL_ADAPTER, RSM_POSITIONING, LIST, GEOSPARQL

OUTPUT_NAMESPACE = 'http://example.org/railML3.2_import#'

RAILML32_DEFAULT_OUTPUT_FOLDER = os.path.join(os.path.curdir, 'TestOutputs')  # default output directory


class Railml32ToRsm:
    def __init__(self):
        self._root = None
        self.input_path = None
        self._output_directory = None
        self._output_path = None  # read-only property
        self._short_name = ''
        self._input_namespaces = None
        self._graph = None
        self._spotElementProjections: dict = {}  # key = IC railML identifier, value = coordinates (X,Y) on canvas or...
        self._spotElementProjectionsPositioningSystemRef = ''  # expect instance of PositioningSystem
        # self.issue_warning_about_distribution()
        print(f"Current directory: {os.path.abspath(os.path.curdir)}")

    def process_railML32(self, input_path: str, output_directory: str, short_name: str = ''):
        """
        :param short_name: for the output file. If not provided, the input file base name shall be kept.
        :param input_path:
        :param output_directory:
        :return:
        """
        # Loading
        self.input_path = input_path
        self.output_directory = output_directory
        self._short_name = short_name
        print(self._load_source(input_path))
        self._graph = Graph()
        self._graph.bind('rsm_topo', RSM_TOPOLOGY)
        self._graph.bind('rsm_geosparql', RSM_GEOSPARQL_ADAPTER)
        self._graph.bind('rsm_positioning', RSM_POSITIONING)
        self._graph.bind('list', LIST)
        self._graph.bind('geo', GEOSPARQL)
        self._graph.bind('', OUTPUT_NAMESPACE)

        # Processing
        print(self._process_net_elements())
        self._process_net_relations()

        # Saving
        self._save_graph_to_file()

    def _load_source(self, path: str) -> str:
        """
        :param path: str, path to the source code file to be loaded
        :return: str, message indicating success or failure
        """
        try:
            tree = etree.parse(path)
            self._root = tree.getroot()
            # print(etree.tostring(self._root, pretty_print=True).decode())
            self.input_namespaces = {k: v for k, v in self._root.nsmap.items() if k}
            # and the lousy one with a None key:
            self._input_namespaces['default'] = list(self._root.nsmap.items())[0][1]
            print(f"INFO: loaded namespaces: {self.input_namespaces}")
            return f"INFO: successfully loaded railML3.2 file: {path}"
        except (OSError, etree.XMLSyntaxError) as e:
            return f"ERROR: Error loading XML file: {e}"

    def _process_net_elements(self):
        """Extracts all net elements in source file."""
        self._process_visualizations()
        self._process_linear_elements()
        self._process_nonlinear_elements()
        self._process_net_relations()
        return f"INFO: output {len(self._graph)} triples."

    def _process_linear_elements(self):

        """
        Loop through net elements.
        :return: info message
        """
        all_net_elements = self._root.findall(".//default:netElement", namespaces=self.input_namespaces)
        print(f"INFO: {len(all_net_elements)} net elements found using findall and namespace prefix. Processing...")
        linear_elements = self._root.findall(".//default:netElement[@length]", namespaces=self.input_namespaces)
        # note: syntax [@length and not(@elementCollection)], while legal XPath1.0, is not accepted by lxml...
        print(f"INFO: {len(linear_elements)} linear elements found. Processing...")
        valid_elements = []
        warnings = []

        # TODO: get rid of @*[local-name()='whatever'] hack

        for element in linear_elements:
            element_id = element.xpath("@*[local-name()='id']")[0]
            length_attr = element.xpath("@*[local-name()='length']")[0]
            if not length_attr:
                warnings.append(
                    f"WARNING: netElement without @length found: {etree.tostring(element, pretty_print=True).decode()}")

            # Create arguments for triples
            element_uri = URIRef(OUTPUT_NAMESPACE + element_id)
            length_value = Literal(length_attr, datatype=XSD.float)
            # Add the LinearElement and its properties to the RDF graph
            self._graph.add((element_uri, RDF.type, RSM_TOPOLOGY.LinearElement))
            self._graph.add((element_uri, RSM_GEOSPARQL_ADAPTER.hasNominaMetriclLength, length_value))
            # Add ports 0 and 1
            for index in range(2):
                port_uri = self.port_uri_ref(element_uri, index)
                self._graph.add((port_uri, RDF.type, RSM_TOPOLOGY.Port))
                self._graph.add((element_uri, RSM_TOPOLOGY.hasPort, port_uri))

            # add positioning systems
            associated_positioning_system = element.xpath("*[local-name()='associatedPositioningSystem']")[0]
            # associated_positioning_system_label = associated_positioning_system.attrib["id"]
            associated_positioning_system_coords = associated_positioning_system.xpath(
                "*[local-name()='intrinsicCoordinate']")
            element_ics = {}  # key: id in railML, value: intrinsicCoord [value of]
            for ic in associated_positioning_system_coords:
                element_ics[ic.attrib["id"]] = ic.attrib["intrinsicCoord"]

            # generate positioning system-related triples.
            # we choose to have positioning systems as blank nodes.
            previous_position, head_position = None, None
            for index, ic in enumerate(element_ics.items()):
                associated_position = BNode()
                self._graph.add((associated_position, RDF.type, RSM_POSITIONING.AssociatedPosition))

                # fetch matching coordinates in canvas or other positioning system
                position = None
                # add the reference system [provisional]
                uriref = OUTPUT_NAMESPACE + 'Canvas'
                if (identifier := ic[0]) in self._spotElementProjections:
                    x, y = self._spotElementProjections[identifier]
                    position = f"<{uriref}> POINT({str(x)} {str(y)})"

                    # self._graph.add(
                    #     (associated_position, RDFS.label, Literal(self._spotElementProjectionsPositioningSystemRef)))

                if index == 0:
                    head_position = associated_position
                    # self._graph.add((associated_position, RDFS.label, Literal(associated_positioning_system_label)))
                else:
                    self._graph.add((previous_position, LIST.hasNext, associated_position))

                self._graph.add(
                    (associated_position, RSM_POSITIONING.intrinsicCoordinate, Literal(ic[1], datatype=XSD.float)))
                if position:
                    self._graph.add(
                        (associated_position, RSM_POSITIONING.position,
                         Literal(position, datatype=GEOSPARQL.wktLiteral)))

                if index == len(associated_positioning_system_coords) - 1:
                    self._graph.add((associated_position, LIST.hasNext, LIST.EmptyList))
                previous_position = associated_position

            self._graph.add((element_uri, RSM_POSITIONING.associatedPositioningSystem, head_position))
            
            # create associated geometry from the associated positions
            # currently, we assume that all points refer to the same referencing system
            # TODO: assemble positions into linestrings according to *multiple* referenced CRS
            associated_positions = []
            # starting with head_position, fetch all position property values and append them to associated_positions
            current_position = head_position
            while current_position and current_position != LIST.EmptyList:
                pos_literal = self._graph.value(current_position, RSM_POSITIONING.position)
                if pos_literal:
                    associated_positions.append(pos_literal)
                current_position = self._graph.value(current_position, LIST.hasNext)
            linestring = self.assemble_wkt_points_to_wkt_linestring(*associated_positions)
            geometry_uri = URIRef(element_uri+'_geometry')
            self._graph.add((geometry_uri, RDF.type, RSM_GEOSPARQL_ADAPTER.Geometry))
            self._graph.add((element_uri, RSM_GEOSPARQL_ADAPTER.hasGeometry, geometry_uri))
            self._graph.add((geometry_uri, GEOSPARQL.asWKT, Literal(linestring, datatype=GEOSPARQL.wktLiteral)))


            # Collect valid elements for the output message
            valid_elements.append(element_uri)

        for warning in warnings:
            print(warning)

        return f"INFO: processed {len(valid_elements)} linear net elements with 'length' attribute."

    def _process_nonlinear_elements(self):
        """

        :return:
        """
        pass

    def _process_net_relations(self):
        """

        :return:
        """
        net_relations = self._root.findall(".//default:netRelations", namespaces=self.input_namespaces)[0]
        for relation in net_relations:
            navigability = relation.attrib["navigability"]
            positionOnA = str(relation.attrib["positionOnA"])
            positionOnB = str(relation.attrib["positionOnB"])
            element_A_ref = OUTPUT_NAMESPACE + relation.xpath("*[local-name()='elementA']")[0].attrib["ref"]
            element_B_ref = OUTPUT_NAMESPACE + relation.xpath("*[local-name()='elementB']")[0].attrib["ref"]
            self._graph.add((self.port_uri_ref(element_A_ref, positionOnA), RSM_TOPOLOGY.connectedWith,
                             self.port_uri_ref(element_B_ref, positionOnB)))
            if navigability == "Both":
                self._graph.add((self.port_uri_ref(element_A_ref, positionOnA), RSM_TOPOLOGY.navigableTo,
                                 self.port_uri_ref(element_B_ref, self.opposite_port(positionOnB))))
                self._graph.add((self.port_uri_ref(element_B_ref, positionOnB), RSM_TOPOLOGY.navigableTo,
                                 self.port_uri_ref(element_A_ref, self.opposite_port(positionOnA))))
            elif navigability == "None":
                self._graph.add((self.port_uri_ref(element_A_ref, positionOnA), RSM_TOPOLOGY.nonNavigableTo,
                                 self.port_uri_ref(element_B_ref, self.opposite_port(positionOnB))))
                self._graph.add((self.port_uri_ref(element_B_ref, positionOnB), RSM_TOPOLOGY.nonNavigableTo,
                                 self.port_uri_ref(element_A_ref, self.opposite_port(positionOnA))))

    def _process_visualizations(self):
        """
        'Visualizations' is the railML3.2 term (and element, in XML) for geometry representation on a canvas.
        Transposed to sRSM, this means using a rsm:Geometry (subclass of geosparql:Geometry) and
        put a reference to the engineering coordinate system in the WKT string.
        """
        visualizations = self._root.findall(".//default:visualizations", namespaces=self.input_namespaces)[0]
        infrastructureVisualizations = visualizations.xpath("*[local-name()='infrastructureVisualizations']")[0]
        infrastructureVisualization = infrastructureVisualizations.xpath(
            "*[local-name()='infrastructureVisualization']")
        if (length := len(infrastructureVisualization)) > 1:
            print(f"WARNING: {length} infrastructure visualizations found. Only the first one will be processed.")
        infrastructureVisualization = infrastructureVisualization[0]
        # id = infrastructureVisualization.attrib["id"]
        self._spotElementProjectionsPositioningSystemRef = infrastructureVisualization.attrib[
            "positioningSystemRef"]  # in the simple example, the canvas
        spotElementProjections = infrastructureVisualization.xpath("*[local-name()='spotElementProjection']")  # a list
        for spotElementProjection in spotElementProjections:
            # we do not exploit the "id" for the time being
            refersTo = spotElementProjection.attrib["refersToElement"]
            # read the coords in element "coordinate"
            coordinate = spotElementProjection.xpath("*[local-name()='coordinate']")
            if len(coordinate) > 0:
                self._spotElementProjections[refersTo] = coordinate[0].attrib["x"], coordinate[0].attrib["y"]

    def _save_graph_to_file(self):
        """
        Serializes the RDFLib graph to a Turtle (.ttl) file in the output directory.
        """
        try:
            self._graph.serialize(destination=self.output_path, format='turtle')
            print(f"INFO: RDF graph successfully saved to {self.output_path}")
        except Exception as e:
            print(f"ERROR: Failed to save RDF graph to {self.output_path}: {e}")

    def _generate_output_path(self, short_name: str) -> str:
        if short_name:
            return os.path.join(self.output_directory, f"{short_name}.ttl")
        return os.path.join(self.output_directory, f"{os.path.basename(self.input_path)}.ttl")

    @property
    def input_namespaces(self):
        return self._input_namespaces

    @input_namespaces.setter
    def input_namespaces(self, value: dict):
        self._input_namespaces = value if value else {}

    @property
    def output_directory(self):
        return self._output_directory

    @output_directory.setter
    def output_directory(self, value: str):
        self._output_directory = value if value else RAILML32_DEFAULT_OUTPUT_FOLDER
        if not os.path.exists(self._output_directory):
            try:
                os.makedirs(self._output_directory)
            except OSError as e:
                print(f"ERROR: could not create {self._output_directory}: {e}")

    @property
    def output_path(self):
        return self._output_path if self._output_path else self._generate_output_path(self._short_name)

    @staticmethod
    def issue_warning_about_distribution():
        user_input = input("WARNING: you may not *distribute* the output file. Type 'YES' to continue: ")
        if user_input == 'YES':
            print("Good girl|boy|whatever. Let us resume.")
        else:
            print("Naughty girl|boy|whatever. Let us stop here.")
            exit()

    @staticmethod
    def port_uri_ref(linear_element_id: str, port_index: str | int) -> URIRef:
        return URIRef(f"{linear_element_id}_port_{str(port_index)}")

    @staticmethod
    def opposite_port(x: str) -> str:
        if x == '0':
            return '1'
        elif x == '1':
            return '0'
        else:
            raise ValueError(f"opposite_port(): Port index {x} is not valid.")

    @staticmethod
    def assemble_wkt_points_to_wkt_linestring(*points: str) -> str:
        """takes as argument a sequence of points in the shape 
        "<reference_system_uri> POINT(<x> <y>)"
        returns "<reference_system_uri> LINESTRING(<x1> <y1>, <x2> <y2>, ...)"
        issues an error if reference systems are not identical.
        """
        if not points:
            raise ValueError("No points provided to assemble WKT LINESTRING.")

        first_ref_sys = None
        point_coords = []

        for point in points:
            if not point.startswith("<") or ">" not in point or "POINT(" not in point:
                raise ValueError(f"Invalid point format: {point}")

            ref_sys, coords = point.split(" POINT(")
            ref_sys = ref_sys.strip("<>")

            if first_ref_sys is None:
                first_ref_sys = ref_sys

            if ref_sys != first_ref_sys:
                raise ValueError("Reference systems are not identical.")

            point_coords.append(coords.rstrip(")"))

        linestring = f"<{first_ref_sys}> LINESTRING({', '.join(point_coords)})"
        return linestring


if __name__ == "__main__":
    RAILML32_TEST_DATA_FOLDER = os.path.join(os.path.curdir, 'TestData')
    railml32_to_rsm = Railml32ToRsm()
    railml32_to_rsm.process_railML32(
        os.path.join(RAILML32_TEST_DATA_FOLDER, "Advanced Example railML.org.xml"),
        RAILML32_DEFAULT_OUTPUT_FOLDER
    )
