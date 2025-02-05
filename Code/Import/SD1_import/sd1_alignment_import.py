"""import the track alignment information of the CCS/TMS (SD1) model using IFC Alignment in its RDF/OWL version.
One IfcAlignment instance is created for each single Linear Element (this is not imposed by IFC, but a RSM)."""

import numpy as np
import rdflib
from rdflib import RDF, BNode, XSD
from rdflib.term import URIRef, Literal

from Import.SD1_import.helper_classes import SubGraph
from Import.SD1_import.helper_functions import timestamp_from_date, azimuth_to_direction, arc_end_coords
from cdm_namespaces import IFC_NAMESPACE, SD1_NAMESPACE, IFC_ADAPTER_NAMESPACE, create_uri, extract_identifier
from sd1_keys import *


class AlignmentGraph(SubGraph):
    def __init__(self, graph: rdflib.Graph, infra_dict: dict, map_dict: dict):
        super().__init__(graph)
        self._trackedge_length_dict = {}  # key: URIRef, value: float, in millimeter (as per SD1 model definition)
        self.infra_dict = infra_dict
        self.trackedge_projection_list = map_dict[TRACK_EDGE_PROJECTIONS_KEY][TRACK_EDGE_PROJECTION_KEY]
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
        return self.infra_dict[GEOMETRY_AREAS_KEY][GEOMETRY_AREA_KEY]

    @property
    def trackedge_geometry_list(self):
        return self.geometry_area[TRACK_EDGE_GEOMETRIES_KEY][TRACK_EDGE_GEOMETRY_KEY]

    @property
    def trackedge_geometry_area_id(self):
        return self.geometry_area['@id']

    @property
    def is_3D(self):
        return True if self.geometry_area[ALIGNMENT_3D_KEY] == 'true' else False

    @property
    def trackedge_geometry_dict(self):
        """has four items, keys being: @id, ns0:horizontalAlignment, ns0:verticalAlignment, ns0:cantPoints"""
        return {trackedge['@id']: trackedge for trackedge in self.trackedge_geometry_list}

    @property
    def trackedge_projection_dict(self):
        return {trackEdgeProjection['@id']: trackEdgeProjection for trackEdgeProjection in
                self.trackedge_projection_list}

    def compute_trackedge_length_dict(self) -> dict:
        trackedge_list = self.infra_dict[TOPO_AREAS_KEY][TOPO_AREA_KEY][TRACK_EDGES_KEY][TRACK_EDGE_KEY]
        trackedge_length_dict = {create_uri(trackedge['@id'], SD1_NAMESPACE): float(trackedge['@trackEdgeLength']) for trackedge
                                 in trackedge_list}
        return trackedge_length_dict

    def get_context_info(self):
        self.RelNestName = 'geometry_area_' + self.trackedge_geometry_area_id
        # this one will be targeted by many properties:
        self.OwnerHistory = create_uri('alignment-data-last-owned-by', SD1_NAMESPACE)
        self._add_owner_history_triples()

    def _add_owner_history_triples(self):
        self.add_triple(self.OwnerHistory, RDF.type, IFC_NAMESPACE.IfcOwnerHistory)
        creation_date = self.infra_dict[GEOMETRY_AREAS_KEY][GEOMETRY_AREA_KEY]['@versionTimestamp']
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

        horizontal_geometry_list = trackedge_geometry_dict[HORIZONTAL_ALIGNMENT_KEY][HORIZONTAL_ALIGNMENT_ITEM_KEY]
        if not isinstance(horizontal_geometry_list, list):  # case of a single dict instead of a list of dicts
            horizontal_geometry_list = [horizontal_geometry_list]

        trackedge_length = self.trackedge_length_dict[trackedge_uri]
        trackedge_start_coordinates = self.get_start_coordinates(trackedge_uri)
        self.generate_horizontal_alignment(this_horizontal_alignment_uri, horizontal_geometry_list, trackedge_length,
                                           trackedge_start_coordinates)
        if is_3d:
            self.generate_vertical_alignment()

    def generate_horizontal_alignment(self, alignment_uri: URIRef, segment_geometry_list: list[dict],
                                      trackedge_length: float, start: tuple[float, float]):
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
        previous_segment_uri, previous_segment_params_uri = None, None
        previous_pos, previous_start_coords, previous_azimuth, previous_segment_length = None, None, None, None
        previous_radius = None

        for segment_geometry in segment_geometry_list:
            # Create segment individual
            segment_uri = create_uri(extract_identifier(alignment_uri) + f'_segment_{index}', SD1_NAMESPACE)
            self.add_triple(segment_uri, RDF.type, IFC_NAMESPACE.IfcAlignmentSegment)
            self.add_triple(segment_nest_uri, IFC_NAMESPACE.relatedObjects_IfcRelNests, segment_uri)

            # Link from previous segment (in IFC, segments are compounded into a linked list)
            if previous_segment_uri is not None:
                self.add_triple(previous_segment_uri, IFC_NAMESPACE.hasNext, segment_uri)

            # Adjoin design params segment
            segment_params_uri = BNode()
            self.add_triple(segment_params_uri, RDF.type, IFC_NAMESPACE.IfcAlignmentHorizontalSegment)
            self.add_triple(segment_uri, IFC_NAMESPACE.designParameters_IfcAlignmentSegment, segment_params_uri)

            # Handle the various IFC predefined types for segments
            # TODO: complete the handling of all predefined segment types
            if 'ns0:horizontalSegmentLine' in segment_geometry.keys():
                pos, azimuth, radius = self.handle_line_case(segment_params_uri, segment_geometry, start)
            elif 'ns0:horizontalSegmentArc' in segment_geometry.keys():
                pos, azimuth, radius = self.handle_arc_case(segment_params_uri, segment_geometry, start)
            else:
                raise f'ERROR: geometry variant not yet implemented: {next(iter(segment_geometry))}'

            # assign segment length to previous segment
            if previous_pos is not None:
                previous_segment_length = (pos - previous_pos) / 1000.0  # in meter
                self.add_triple(previous_segment_params_uri, IFC_NAMESPACE.segmentLength_IfcAlignmentHorizontalSegment,
                                Literal(previous_segment_length, datatype=XSD.decimal))

            # first segment start point is identical with trackedge start point, otherwise needs to be computed
            if index == 1:
                start_coords = np.array(start)
            else:
                start_coords = arc_end_coords(previous_start_coords, azimuth_to_direction(previous_azimuth),
                                              previous_segment_length, previous_radius)
            self.add_triple(segment_params_uri, IFC_NAMESPACE.startPoint_IfcAlignmentHorizontalSegment,
                            Literal(start_coords))

            # prepare next loop iteration
            index += 1
            previous_segment_uri = segment_uri
            previous_segment_params_uri = segment_params_uri
            previous_pos = pos
            previous_radius = radius
            previous_start_coords = start_coords
            previous_azimuth = azimuth

        # create one last segment with zero length and finish the linked list
        length_of_last_non_zero_segment = (trackedge_length - previous_pos) / 1000  # in meter
        self.add_triple(previous_segment_params_uri, IFC_NAMESPACE.segmentLength_IfcAlignmentHorizontalSegment,
                        Literal(length_of_last_non_zero_segment, datatype=XSD.decimal))
        self.add_triple(previous_segment_uri, IFC_NAMESPACE.hasNext, IFC_NAMESPACE.IfcObjectDefinition_EmptyList)
        previous_end_coords = arc_end_coords(previous_start_coords, azimuth_to_direction(previous_azimuth),
                                             length_of_last_non_zero_segment, previous_radius)
        self.finish_alignment(alignment_uri, previous_segment_uri, previous_end_coords, previous_azimuth)

    def handle_line_case(self, segment_params_uri, segment_geometry, start) -> tuple[float, float, float]:
        """returns the position (expressed in the SD1 linear referencing system) of the start of segment"""
        pos = float(segment_geometry['ns0:horizontalSegmentLine']['@trackGeometryPos'])
        azimuth = float(segment_geometry['ns0:horizontalSegmentLine']['@azimuth'])
        self.add_triple(segment_params_uri, IFC_NAMESPACE.predefinedType_IfcActionRequest, IFC_NAMESPACE.LINE)
        self.generate_alignment_parameter_segment_horizontal(segment_params_uri, azimuth, radius=0)
        return pos, azimuth, 0

    def handle_arc_case(self, segment_params_uri, segment_geometry, start) -> tuple[float, float, float]:
        pos = float(segment_geometry['ns0:horizontalSegmentArc']['@trackGeometryPos'])
        azimuth = float(segment_geometry['ns0:horizontalSegmentArc']['@azimuth'])
        radius = float(segment_geometry['ns0:horizontalSegmentArc']['@radius'])
        self.add_triple(segment_params_uri, IFC_NAMESPACE.predefinedType_IfcActionRequest, IFC_NAMESPACE.CIRCULARARC)
        self.generate_alignment_parameter_segment_horizontal(segment_params_uri, azimuth, radius)
        return pos, azimuth, radius

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
            coord_list = coords[COORDINATES_KEY][COORDINATE_KEY]
            if coord_list:
                result = (float(coord_list[0]['@x']), float(coord_list[0]['@y']))
        return result

    def finish_alignment(self, alignment_uri, previous_segment_uri, previous_end_coords, previous_end_azimuth):
        # add zero length segment in order to record the end position of the previous "real" segment
        zero_length_segment_uri = create_uri(extract_identifier(alignment_uri) + '_zero_length_segment', SD1_NAMESPACE)
        self.add_triple(zero_length_segment_uri, RDF.type, IFC_NAMESPACE.IfcAlignmentSegment)

        # associate parameters node
        zero_length_segment_horizontal_params = BNode()
        self.add_triple(zero_length_segment_horizontal_params, RDF.type, IFC_NAMESPACE.IfcAlignmentHorizontalSegment)
        self.add_triple(zero_length_segment_uri, IFC_NAMESPACE.designParameters_IfcAlignmentSegment,
                        zero_length_segment_horizontal_params)

        # parameters values
        self.add_triple(zero_length_segment_horizontal_params, IFC_NAMESPACE.startPoint_IfcAlignmentHorizontalSegment,
                        Literal(previous_end_coords))
        self.add_triple(zero_length_segment_horizontal_params,
                        IFC_NAMESPACE.segmentLength_IfcAlignmentHorizontalSegment, Literal(0, datatype=XSD.decimal))
        self.add_triple(zero_length_segment_horizontal_params,
                        IFC_NAMESPACE.predefinedType_IfcAlignmentHorizontalSegment, IFC_NAMESPACE.LINE)
        self.generate_alignment_parameter_segment_horizontal(zero_length_segment_horizontal_params,
                                                             previous_end_azimuth, radius=0)

        # link previous segment with zero-length segment
        self.add_triple(previous_segment_uri, IFC_NAMESPACE.hasNext, zero_length_segment_uri)

        # finally, link last, zero-length element with an empty object (as per IFC)
        empty_obj = BNode()
        self.add_triple(empty_obj, RDF.type, IFC_NAMESPACE.IfcObjectDefinition_EmptyList)
        self.add_triple(zero_length_segment_uri, IFC_NAMESPACE.hasNext, empty_obj)

    def export_as_enz(self, out_path: str, comma_separated=True):
        """export the alignment as an ENZ file (Easting, Northing, Z) for further processing, e.g. in AUTOCAD
        or Civil 3D.
        The ENZ file consists in a sequence of points delimiting the alignment segments.
        On that basis, applications such as Civil 3D (Autodesk) or Bentley OpenRail Designer may compute
        the best fit alignment (using straight lines, arcs, and spirals = transition curves).
        ENZ files are text files: <easting><sep><northing><sep><altitude><line break>... where <sep> is a user-defined
        separator, and easting etc. values are expressed as floats."""
        pass
