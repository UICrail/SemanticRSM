# This module will take into account the "slip crossing" or "slip switch" functionality that can be found in
# the provided GeoJSON file as an annotation to artificial linear elements.
# These artefacts are produced in the course of the drawIO-to-GeoJSON conversion (see drawIO_import folder).
# The effect of the module is to
# 1 - add navigabilities corresponding to the slip switch function;
# 2 - remove the artificial linear elements used to express this function.
