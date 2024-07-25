Import modules from CCS/TMS (SD1) sources.

Valid for CCS/TMS model version 0.4.2 (July 2024)

Imported files:
* infra.xml
  * topo area: done
  * geometry area: done
  * sampled geometry area: probably not for CDM (application-specific, derived data)
  * functional area: partly imported for deriving navigabilities
  * properties area: TBD
  * track usage area: TBD
* map.xml : locates trackedges and functional elements on a cartesian reference system. The EPSG code of the coordinate reference system is foreseen to be provided, but value 0 is obviously incorrect.
* 