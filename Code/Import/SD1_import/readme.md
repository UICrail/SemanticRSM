Import modules from CCS/TMS (SD1) sources.

Valid for CCS/TMS model version 1.0 (December 2024)

# Import status
* infra.xml
  * topo area: done
  * geometry area: done
  * sampled geometry area: probably not for CDM (application-specific, derived data with unpublished, vendor-specific derivation rules)
  * functional area: used for deriving navigabilities. To be done: instantiation of net entities (switches, crossings)
  * properties area: TBD
  * track usage area: TBD
* map.xml : locates trackedges and functional elements on a cartesian reference system. The EPSG code of the coordinate reference system is foreseen to be provided, but value 0 is obviously incorrect.
  * map area
    * track edge projections: the first point of each trackedge is used for computing the Ifc Alignment segment start points

# Comments
The import is rather uneventful, as the CCS/TMS data model borrows many elements from CDM models. Examples:
* CCS/TMS track edges are equivalent to CDM/RSM linear elements at micro level
* CCS/TMS geometry (not to be confused with: sampled geometry) matches IFC Alignment classes pretty well. The provided sample data are however questionable.

On the other hand, CCS/TMS elements are "packaged" differently; for instance:
* Most IFC Alignment information can be found in the infrastructure / geometry area, except for the track edge element start (and end) coordinates that are in the map area
* Most CDM/RSM topology information can be found in infrastructure / topo area, except for the navigabilities that are stored in infra / functional area / simple point, slip crossings, crossings area

Elements and attributes names in the CCS/TMS XSD differ from class and property names in the original models, and the presence of reserved characters in identifiers requires some changes to turn them into valid URIs
(most common case bein white space ' ', to be encoded as '%20')