import rdflib
from rdflib import RDF, BNode, XSD
from rdflib.term import URIRef, Literal

from Import.SD1_import.helper_classes import SubGraph
from Import.SD1_import.helper_functions import timestamp_from_date, azimuth_to_direction
from cdm_namespaces import IFC_NAMESPACE, SD1_NAMESPACE, IFC_ADAPTER_NAMESPACE, create_uri, extract_identifier


class AlignmentGraph(SubGraph):
    def __init__(self, graph: rdflib.Graph, infra_dict: dict, map_dict: dict):
        super().__init__(graph)
        self._trackedge_length_dict = {}  # key: URIRef, value: float, in millimeter
        self.infra_dict = infra_dict
        self.trackedge_projection_list = map_dict['ns0:trackEdgeProjections']['ns0:trackEdgeProjection']
        self.IfcRelNests_IfcAlignment: BNode | None = None  # links IfcAlignmentHorizontal etc. to IfcAlignment
        self.IfcRelNests_IfcAlignmentSegment: BNode | None = None  # links segments to IfcAlignmentHorizontal
        # attributes for IfcRelNests instances, extracted from geometryArea
        self.RelNestName: IFC_NAMESPACE.IfcLabel | None = None
        self.OwnerHistory: URIRef | None = None

    @property
    def trackedge_length_dict(self):
        if not self._trackedge_length_dict:
            self._trackedge_length_dict = self.compute_trackedge_length_dict()
        return self._trackedge_length_dict

    @property
    def geometry_area(self):
        return self.infra_dict['ns0:geometryAreas']['ns0:geometryArea']

    @property
    def trackedge_geometry_list(self):
        return self.geometry_area['ns0:trackEdgeGeometries']['ns0:trackEdgeGeometry']

    @property
    def trackedge_geometry_area_id(self):
        return self.geometry_area['@id']

    @property
    def is_3D(self):
        return True if self.geometry_area['@alignment3d'] == 'true' else False

    @property
    def trackedge_geometry_dict(self):
        """has four items, keys being: @id, ns0:horizontalAlignment, ns0:verticalAlignment, ns0:cantPoints"""
        return {trackedge['@id']: trackedge for trackedge in self.trackedge_geometry_list}

    @property
    def trackedge_projection_dict(self):
        return {trackEdgeProjection['@id']: trackEdgeProjection for trackEdgeProjection in
                self.trackedge_projection_list}

    def compute_trackedge_length_dict(self) -> dict:
        trackedge_list = self.infra_dict['ns0:topoAreas']['ns0:topoArea']['ns0:trackEdges']['ns0:trackEdge']
        trackedge_length_dict = {create_uri(trackedge['@id'], SD1_NAMESPACE): float(trackedge['@length']) for trackedge
                                 in trackedge_list}
        return trackedge_length_dict

    def get_context_info(self):
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

    def generate_alignments(self):
        for trackedge, trackedge_geometry_dict in self.trackedge_geometry_dict.items():
            self.generate_alignment(create_uri(trackedge, SD1_NAMESPACE), trackedge_geometry_dict, self.is_3D)

    def generate_alignment(self, trackedge_uri: URIRef, trackedge_geometry_dict: dict, is_3d: bool = False):
        """Creates the IFC alignment corresponding to the given track edge (linear element at micro level)"""
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

        horizontal_geometry_list = trackedge_geometry_dict['ns0:horizontalAlignment']['ns0:horizontalAlignmentItem']
        if not isinstance(horizontal_geometry_list, list):  # case of a single dict instead of a list of >1 dict
            horizontal_geometry_list = [horizontal_geometry_list]

        trackedge_length = self.trackedge_length_dict[trackedge_uri]
        trackedge_start_coordinates = self.get_start_coordinates(trackedge_uri)
        self.generate_horizontal_alignment(this_horizontal_alignment_uri, horizontal_geometry_list, trackedge_length,
                                           trackedge_start_coordinates)
        if is_3d:
            self.generate_vertical_alignment()

    def generate_horizontal_alignment(self, alignment_uri: URIRef, segment_geometry_list: list[dict],
                                      trackedge_length: float, start_coords: tuple[float, float]):
        """Creates the IFC alignment segments and their parameters, corresponding to one track edge (linear element)"""
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
            # first segment start is identical with trackedge start
            if index == 1:
                start=start_coords
            else:
                #TODO: insert computation of start of next segment = end of previous
                start = None
            if 'ns0:line' in segment_geometry.keys():
                # straight line case
                pos = self.handle_line_case(segment_params_uri, segment_geometry, start)
            elif 'ns0:arc' in segment_geometry.keys():
                # circular arc case
                pos = self.handle_arc_case(segment_params_uri, segment_geometry, start)
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

        # finally, deal with last segment, linking it to an empty object (as per IFC)
        # TODO: IFC alignment suggests to use zero-length element instead, not telling why. Check. Maybe that's to have the StartPoint of that last element acting as an endpoint to the segment chain...
        empty_obj = BNode()
        self.add_triple(empty_obj, RDF.type, IFC_NAMESPACE.IfcObjectDefinition_EmptyList)
        self.add_triple(previous_segment_uri, IFC_NAMESPACE.hasNext, empty_obj)
        # add length of last segment
        length_of_last_segment = (trackedge_length - previous_pos) / 1000  # in meter
        self.add_triple(previous_segment_params_uri, IFC_NAMESPACE.segmentLength_IfcAlignmentHorizontalSegment,
                        Literal(length_of_last_segment, datatype=XSD.decimal))

    def handle_line_case(self, segment_params_uri, segment_geometry, start) -> float:
        """returns the position (expressed in the SD1 linear referencing system) of the start of segment"""
        pos = float(segment_geometry['ns0:line']['@pos'])
        azimuth = float(segment_geometry['ns0:line']['@azimuth']) / 1000.0
        self.add_triple(segment_params_uri, IFC_NAMESPACE.predefinedType_IfcActionRequest, IFC_NAMESPACE.LINE)
        self.generate_alignment_parameter_segment_horizontal(segment_params_uri, azimuth, radius=0, start=start)
        return pos

    def handle_arc_case(self, segment_params_uri, segment_geometry, start) -> float:
        pos = float(segment_geometry['ns0:arc']['@pos'])
        azimuth = float(segment_geometry['ns0:arc']['@azimuth']) / 1000.0
        radius = float(segment_geometry['ns0:arc']['@radius'])
        self.add_triple(segment_params_uri, IFC_NAMESPACE.predefinedType_IfcActionRequest, IFC_NAMESPACE.CIRCULARARC)
        self.generate_alignment_parameter_segment_horizontal(segment_params_uri, azimuth, radius, start=start)
        return pos

    def generate_vertical_alignment(self):
        # currently no data, so we leave that empty
        # TODO: write code for generating vertical alignment
        pass

    def generate_alignment_parameter_segment_horizontal(self, node: BNode, azimuth: float, radius: float = 0.0,
                                                        start: tuple[float, float] | None = None):
        """Applicable to lines and circular arcs. Copies args from SD1 source and infers the rest.
        :param start:
        :param node: blank node for segment parameters
        :param azimuth: azimuth angle in degrees (WRT true North)
        :param radius: (start) radius of curvature in mm (check sign; IFC convention is <0 for clockwise turn, 0 for infinity)"""

        self.add_triple(node, IFC_NAMESPACE.startDirection_IfcAlignmentHorizontalSegment,
                        Literal(azimuth_to_direction(azimuth), datatype=XSD.decimal))
        self.add_triple(node, IFC_NAMESPACE.startRadiusOfCurvature_IfcAlignmentHorizontalSegment,
                        Literal(radius / 1000, datatype=XSD.decimal))
        self.add_triple(node, IFC_NAMESPACE.endRadiusOfCurvature_IfcAlignmentHorizontalSegment,
                        Literal(radius / 1000, datatype=XSD.decimal))
        if start is None:
            self.add_triple(node, IFC_NAMESPACE.startPoint_IfcAlignmentHorizontalSegment,
                            Literal("not available in source file", datatype=XSD.string))
        else:
            self.add_triple(node, IFC_NAMESPACE.startPoint_IfcAlignmentHorizontalSegment, Literal(start))

    def generate_cartesian_point(self, point_node: BNode, easting: float, northing: float, epsg_code: str = ''):
        """"""
        self.add_triple(point_node, RDF.type, IFC_NAMESPACE.IfcCartesianPoint)
        self.add_triple(point_node, IFC_NAMESPACE.coordinates_IfcCartesianPoint, Literal(f'({easting},  {northing})'))

    def get_start_coordinates(self, trackedge_uriref: URIRef) -> tuple[float, float] | None:
        """computes start (projected) coordinate of a trackedge. Will be used to compute the start of each segment"""
        result = None
        # get track edge ID back
        trackedge_sd1id = extract_identifier(trackedge_uriref)
        if (coords := self.trackedge_projection_dict.get(trackedge_sd1id)) is not None:
            coord_list = coords['ns0:coordinates']['ns0:coordinate']
            if coord_list:
                result = (float(coord_list[0]['@x']), float(coord_list[0]['@y']))
        return result
