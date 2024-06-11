% This module reads the Ventimiglia-Albenga RDF file
:- use_module(library(semweb/rdf11)) .   
:- use_module(library(semweb/rdf_http_plugin)).
:- use_module(library(semweb/rdf_turtle)) .
:- set_prolog_flag(verbose_load, true).
:- debug(http(load)).

:- rdf_load('http://cdm.ovh/examples/Ventimiglia-Albenga/osm_Ventimiglia-Albenga_with_navigabilities.ttl').
:- debug(rdf_query) .
:- rdf('http://cdm.ovh/examples/Ventimiglia-Albenga/osm_Ventimiglia-Albenga_with_navigabilities#jointline_241-56-238-239_port_1', rdf:type, 'http:/cdm.ovh/rsm/topology/topology#Port') .