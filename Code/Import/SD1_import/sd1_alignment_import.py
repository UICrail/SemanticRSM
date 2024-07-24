import rdflib
from rdflib import RDF, BNode, XSD
from rdflib.term import URIRef, Literal

from Import.SD1_import.helper_classes import SubGraph
from Import.SD1_import.helper_functions import timestamp_from_date, azimuth_to_direction
from cdm_namespaces import IFC_NAMESPACE, SD1_NAMESPACE, IFC_ADAPTER_NAMESPACE, create_uri, extract_identifier


class AlignmentGraph(SubGraph):
    def __init__(self, graph: rdflib.Graph, infra_dict: dict, origin_easting: float, origin_northing: float):
        super().__init__(graph)
        self.infra_dict = infra_dict
        self.trackedge_length_dict = self.get_trackedge_length_dict()  # key: URIRef, value: float, in millimeter
        self.IfcRelNests_IfcAlignment: BNode | None = None  # links IfcAlignmentHorizontal etc. to IfcAlignment
        self.IfcRelNests_IfcAlignmentSegment: BNode | None = None  # links segments to IfcAlignmentHorizontal
        # attributes for IfcRelNests instances, extracted from geometryArea
        self.RelNestName: IFC_NAMESPACE.IfcLabel | None = None
        self.OwnerHistory: URIRef | None = None
        self.OriginGridCoordinates = (origin_easting, origin_northing)

    @property
    def trackedge_geometry_list(self):
        return self.infra_dict['ns0:geometryAreas']['ns0:geometryArea']['ns0:trackEdgeGeometries'][
            'ns0:trackEdgeGeometry']

    @property
    def geometry_area(self):
        return self.infra_dict['ns0:geometryAreas']['ns0:geometryArea']

    @property
    def trackedge_geometry_area_id(self):
        return self.geometry_area['@id']

    @property
    def is_3D(self):
        return True if self.infra_dict['ns0:geometryAreas']['ns0:geometryArea']['@alignment3d'] == 'true' else False

    @property
    def trackedge_geometry_dict(self):
        """has four items, keys being: @id, ns0:horizontalAlignment, ns0:verticalAlignment, ns0:cantPoints"""
        return {trackedge['@id']: trackedge for trackedge in self.trackedge_geometry_list}

    def get_trackedge_length_dict(self) -> dict:
        trackedge_list = self.infra_dict['ns0:topoAreas']['ns0:topoArea']['ns0:trackEdges']['ns0:trackEdge']
        self.trackedge_length_dict = {}
        for trackedge in trackedge_list:
            self.trackedge_length_dict[create_uri(trackedge['@id'], SD1_NAMESPACE)] = float(trackedge['@length'])
        return self.trackedge_length_dict

    def generate_alignments(self):
        self.RelNestName = 'geometry_area_' + self.trackedge_geometry_area_id
        # this one will be targeted by many properties:
        self.OwnerHistory = create_uri('alignment-data-last-owned-by', SD1_NAMESPACE)
        self.add_triple(self.OwnerHistory, RDF.type, IFC_NAMESPACE.IfcOwnerHistory)
        creation_date = self.infra_dict['ns0:geometryAreas']['ns0:geometryArea']['@versionTimestamp']
        creation_timestamp = timestamp_from_date(creation_date)
        self.add_triple(self.OwnerHistory, IFC_NAMESPACE.CreationDate_IfcOwnerHistory,
                        Literal(creation_timestamp, datatype=XSD.integer))
        owning_user = create_uri('System_Pillar_project_team', SD1_NAMESPACE)
        self.add_triple(owning_user, RDF.type, IFC_NAMESPACE.IfcPersonAndOrganization)
        self.add_triple(self.OwnerHistory, IFC_NAMESPACE.owningUser_IfcOwnerHistory, owning_user)

        for trackedge, trackedge_geometry_dict in self.trackedge_geometry_dict.items():
            self.generate_alignment(create_uri(trackedge, SD1_NAMESPACE), trackedge_geometry_dict, self.is_3D)

    def generate_alignment(self, trackedge_uri: URIRef, geometry_dict: dict, is_3d: bool = False):
        # create IfcAlignment instance (NOT as a blank node, conforming IFC)
        this_alignment_uri = create_uri(extract_identifier(trackedge_uri) + '_alignment', SD1_NAMESPACE)
        self.add_triple(this_alignment_uri, RDF.type, IFC_NAMESPACE.IfcAlignment)

        # link alignment with track edge (RSM linear element in the graph)
        # TODO: include this property (and an inverse property) in the IFC Adapter module to be created
        self.add_triple(trackedge_uri, IFC_ADAPTER_NAMESPACE.hasIfcAlignment, this_alignment_uri)

        # add IfcRelNests individual and link it to alignment
        nest_uri = create_uri(extract_identifier(this_alignment_uri) + '_nest', SD1_NAMESPACE)
        self.add_triple(nest_uri, RDF.type, IFC_NAMESPACE.IfcRelNests)
        self.add_triple(this_alignment_uri, IFC_NAMESPACE.isNestedBy_IfcObjectDefinition, nest_uri)

        # add geometry area info related to this particular trackedge
        # this includes general Geometry Area info, as the Geometry Area is not an IFC concept and
        # was not yet mapped 1:1
        self.add_triple(nest_uri, IFC_NAMESPACE.ownerHistory_IfcRoot, self.OwnerHistory)

        # horizontal alignment is always required

        this_horizontal_alignment_uri = create_uri(extract_identifier(trackedge_uri) + '_horizontal_alignment',
                                                   SD1_NAMESPACE)
        self.add_triple(this_horizontal_alignment_uri, RDF.type, IFC_NAMESPACE.IfcAlignmentHorizontal)
        self.add_triple(nest_uri, IFC_NAMESPACE.relatedObjects_IfcRelNests, this_horizontal_alignment_uri)

        horizontal_geometry_list = geometry_dict['ns0:horizontalAlignment']['ns0:horizontalAlignmentItem']
        if not isinstance(horizontal_geometry_list, list):  # case of a single dict instead of a list of >1 dict
            horizontal_geometry_list = [horizontal_geometry_list]

        trackedge_length = self.trackedge_length_dict[trackedge_uri]
        self.generate_horizontal_alignment(this_horizontal_alignment_uri, horizontal_geometry_list, trackedge_length)
        if is_3d:
            self.generate_vertical_alignment()

    def generate_horizontal_alignment(self, alignment_uri: URIRef, segment_geometry_list: list[dict],
                                      this_trackedge_length: float):
        # TODO: split into general part (usable also by vertical alignment) and specific part (to horizontal align.)

        # create the "nest"
        segment_nest_uri = create_uri(extract_identifier(alignment_uri) + '_nest', SD1_NAMESPACE)
        self.add_triple(segment_nest_uri, RDF.type, IFC_NAMESPACE.IfcRelNests)
        self.add_triple(alignment_uri, IFC_NAMESPACE.isNestedBy_IfcObjectDefinition, segment_nest_uri)

        if not segment_geometry_list:
            obj = BNode()
            self.add_triple(object, RDF.type, IFC_NAMESPACE.IfcObjectDefinition_EmptyList)
            self.add_triple(segment_nest_uri, IFC_NAMESPACE.relatedObjects_IfcRelNests, obj)
            return

        # create the IfcAlignmentSegments and their parameters
        index = 1  # starts with 1, following SD1 conventions
        previous_segment_uri = None
        previous_segment_params_uri = None
        previous_pos = None
        for segment_geometry in segment_geometry_list:
            segment_uri = create_uri(extract_identifier(alignment_uri) + f'_segment_{index}', SD1_NAMESPACE)
            self.add_triple(segment_uri, RDF.type, IFC_NAMESPACE.IfcAlignmentSegment)
            self.add_triple(segment_nest_uri, IFC_NAMESPACE.relatedObjects_IfcRelNests, segment_uri)
            # adjoin design params segment
            segment_params_uri = BNode()
            self.add_triple(segment_params_uri, RDF.type, IFC_NAMESPACE.IfcAlignmentSegmentHorizontal)
            self.add_triple(segment_uri, IFC_NAMESPACE.designParameters_IfcAlignmentSegment, segment_params_uri)
            if 'ns0:line' in segment_geometry.keys():
                # straight line case
                pos = self.handle_line_case(segment_params_uri, segment_geometry)
            elif 'ns0:arc' in segment_geometry.keys():
                # circular arc case
                pos = self.handle_arc_case(segment_params_uri, segment_geometry)
            else:
                raise f'ERROR: geometry variant not yet implemented: {next(iter(segment_geometry))}'
            # add link (segments are a linked list)
            if previous_segment_uri is not None:
                self.add_triple(previous_segment_uri, IFC_NAMESPACE.hasNext, segment_uri)
            # assign segment length to previous segment
            if previous_pos is not None:
                previous_segment_length = (pos - previous_pos) / 1000.0  # in meter
                self.add_triple(previous_segment_params_uri, IFC_NAMESPACE.segmentLength_IfcAlignmentHorizontalSegment,
                                Literal(previous_segment_length, datatype=XSD.decimal))
            # prepare next loop
            index += 1
            previous_segment_uri = segment_uri
            previous_segment_params_uri = segment_params_uri
            previous_pos = pos

        # deal with last segment, linking it to an empty object (as per IFC)
        # TODO: IFC alignment suggests to use zero-length element instead, not telling why. Check.
        empty_obj = BNode()
        self.add_triple(empty_obj, RDF.type, IFC_NAMESPACE.IfcObjectDefinition_EmptyList)
        self.add_triple(previous_segment_uri, IFC_NAMESPACE.hasNext, empty_obj)
        # add length of last segment
        length_of_last_segment = (this_trackedge_length - previous_pos) / 1000  # in meter
        self.add_triple(previous_segment_params_uri, IFC_NAMESPACE.segmentLength_IfcAlignmentHorizontalSegment,
                        Literal(length_of_last_segment, datatype=XSD.decimal))

    def handle_line_case(self, segment_params_uri, segment_geometry) -> float:
        """returns the position (expressed in the SD1 linear referencing system) of the start of segment"""
        pos = float(segment_geometry['ns0:line']['@pos'])
        azimuth = float(segment_geometry['ns0:line']['@azimuth']) / 1000.0
        self.add_triple(segment_params_uri, IFC_NAMESPACE.predefinedType_IfcActionRequest, IFC_NAMESPACE.LINE)
        self.generate_alignment_parameter_segment_horizontal(segment_params_uri, azimuth)
        return pos

    def handle_arc_case(self, segment_params_uri, segment_geometry) -> float:
        pos = float(segment_geometry['ns0:arc']['@pos'])
        azimuth = float(segment_geometry['ns0:arc']['@azimuth']) / 1000.0
        radius = float(segment_geometry['ns0:arc']['@radius'])
        self.add_triple(segment_params_uri, IFC_NAMESPACE.predefinedType_IfcActionRequest, IFC_NAMESPACE.CIRCULARARC)
        self.generate_alignment_parameter_segment_horizontal(segment_params_uri, azimuth, radius)
        return pos

    def generate_vertical_alignment(self):
        # currently no data, so we leave that empty
        # TODO: write code for generating vertical alignment
        pass

    def generate_alignment_parameter_segment_horizontal(self, node: BNode, azimuth: float, radius: float = 0.0):
        """Applicable to lines and circular arcs. Copies args from SD1 source and infers the rest.
        :param node: blank node for segment parameters
        :param azimuth: azimuth angle in degrees (WRT true North)
        :param radius: (start) radius of curvature in mm (check sign; IFC convention is <0 for clockwise turn, 0 for infinity)"""

        self.add_triple(node, IFC_NAMESPACE.startDirection_IfcAlignmentHorizontalSegment,
                        Literal(azimuth_to_direction(azimuth), datatype=XSD.decimal))
        self.add_triple(node, IFC_NAMESPACE.startRadiusOfCurvature_IfcAlignmentHorizontalSegment,
                        Literal(radius / 1000, datatype=XSD.decimal))
        self.add_triple(node, IFC_NAMESPACE.endRadiusOfCurvature_IfcAlignmentHorizontalSegment,
                        Literal(radius / 1000, datatype=XSD.decimal))
        self.add_triple(node, IFC_NAMESPACE.startPoint_IfcAlignmentHorizontalSegment,
                        Literal("to be calculated", datatype=XSD.string))

    def generate_cartesian_point(self, node: BNode, longitude: float, latitude: float, target_epsg: str = "3034"):
        """Assume SD1 geo coords use WGS84 or ETRS89 (deemed equivalent here).
        Not used for the time being, as no (lon, lat) coordinates could be found in the SD1 sample data"""
        import pyproj
        crs_4326 = pyproj.CRS("WGS84")
        target_crs = pyproj.CRS(f"EPSG:{target_epsg}")
        crs_transformer = pyproj.Transformer.from_crs(crs_4326, target_crs, always_xy=True)
        x, y = crs_transformer.transform(longitude, latitude)
        self.add_triple(node, IFC_NAMESPACE.coordinates_IfcCartesianPoint,
                        Literal(f'POINT({x} {y})', datatype=IFC_NAMESPACE.IfcCartesianPoint))
