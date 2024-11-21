from rdflib.namespace import Namespace

# non-CDM namespaces

GEOSPARQL = Namespace("http://www.opengis.net/ont/geosparql#")
LIST = Namespace("http://www.w3.org/ns/list#")

# CDM namespaces


# RSM namespaces

RSM_TOPOLOGY = Namespace("http://cdm.ovh/rsm/topology/0.1/topology#")
RSM_POSITIONING = Namespace("http://cdm.ovh/rsm/positioning/positioning#")
RSM_GEOSPARQL_ADAPTER = Namespace("http://cdm.ovh/rsm/adapters/geosparql_adapter#")

RSM_COMPLETE = Namespace("http://cdm.ovh/rsm/rsm_complete#")

# for sample data, esp. output data

WORK = Namespace("http://cdm.ovh/examples#")
