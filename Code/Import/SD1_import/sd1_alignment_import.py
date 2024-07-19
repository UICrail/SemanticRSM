import rdflib
from rdflib import RDF, BNode, XSD
from rdflib.term import URIRef, Literal

from Import.SD1_import.helper_classes import SubGraph
from Import.SD1_import.helper_functions import timestamp_from_date
from cdm_namespaces import IFC_NAMESPACE, SD1_NAMESPACE, IFC_ADAPTER_NAMESPACE, create_uri, extract_identifier


class AlignmentGraph(SubGraph):
    def __init__(self, graph: rdflib.Graph, infra_dict: dict):
        super().__init__(graph)
        self.infra_dict = infra_dict
        self.IfcRelNests_IfcAlignment: BNode | None = None  # links IfcAlignmentHorizontal etc. to IfcAlignment
        self.IfcRelNests_IfcAlignmentSegment: BNode | None = None  # links segments to IfcAlignmentHorizontal
        # attributes for IfcRelNests instances, extracted from geometryArea
        self.RelNestName: IFC_NAMESPACE.IfcLabel | None = None
        self.OwnerHistory: URIRef | None = None

    def trackedge_geometry_list(self) -> list:
        return self.infra_dict['ns0:geometryAreas']['ns0:geometryArea']['ns0:trackEdgeGeometries'][
            'ns0:trackEdgeGeometry']

    def trackedge_geometry_area_id(self) -> str:
        return self.infra_dict['ns0:geometryAreas']['ns0:geometryArea']['@id']

    def is_3D(self) -> bool:
        return True if self.infra_dict['ns0:geometryAreas']['ns0:geometryArea']['@alignment3d'] == 'true' else False

    def trackedge_geometry_dict(self) -> dict:
        """has four entries, keys: @id, ns0:horizontalAlignment, ns0:verticalAlignment, ns0:cantPoints"""
        return {trackedge['@id']: trackedge for trackedge in self.trackedge_geometry_list()}

    def generate_alignments(self):
        self.RelNestName = 'geometry_area_' + self.trackedge_geometry_area_id()
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

        for trackedge, trackedge_geometry_dict in self.trackedge_geometry_dict().items():
            self.generate_alignment(create_uri(trackedge, SD1_NAMESPACE), trackedge_geometry_dict, self.is_3D())

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

        self.generate_horizontal_alignment(this_horizontal_alignment_uri, horizontal_geometry_list)
        if is_3d:
            self.generate_vertical_alignment()

    def generate_horizontal_alignment(self, alignment_uri: URIRef, segment_geometry_list: list[dict]):
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
        previous_segment_URI = None
        for segment in segment_geometry_list:
            segment_uri = create_uri(extract_identifier(alignment_uri) + f'_segment_{index}', SD1_NAMESPACE)
            self.add_triple(segment_uri, RDF.type, IFC_NAMESPACE.IfcAlignmentSegment)
            self.add_triple(segment_nest_uri, IFC_NAMESPACE.relatedObjects_IfcRelNests, segment_uri)
            # adjoin design params segment
            segment_params_uri = BNode()
            self.add_triple(segment_params_uri, RDF.type, IFC_NAMESPACE.IfcAlignmentSegmentHorizontal)
            self.add_triple(segment_uri, IFC_NAMESPACE.designParameters_IfcAlignmentSegment, segment_params_uri)
            if 'ns0:line' in segment.keys():
                # straight line case
                self.add_triple(segment_params_uri, IFC_NAMESPACE.predefinedType_IfcActionRequest, IFC_NAMESPACE.LINE)
            elif 'ns0:arc' in segment.keys():
                # circular arc case
                self.add_triple(segment_params_uri, IFC_NAMESPACE.predefinedType_IfcActionRequest, IFC_NAMESPACE.CIRCULARARC)
            else:
                raise f'ERROR: geometry variant not yet implemented: {next(iter(segment))}'
            # add chainage
            if previous_segment_URI is not None:
                self.add_triple(previous_segment_URI, IFC_NAMESPACE.hasNext, segment_uri)
            index += 1
            previous_segment_URI = segment_uri

    def generate_vertical_alignment(self):
        # currently no data, so we leave that empty
        pass

    def generate_alignment_parameter_segment_horizontal(self):
        pass
