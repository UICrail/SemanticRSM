# This module handles the "slip switch" aspects of crossings.
# Source file is a GeoJSON file with track segments (linear elements), their labels,
# and possibly slip switch markers.
# a slip switch marker, in the drawIO diagram, is conventionally a dashed line.
# its ends should be close to the extremities of the concerned branches of a crossing.
# Thus a double-slip crossing will sport two such dashed lines.
# Relevant to the processing is only:
#  - the "dashed" property of the segment;
#  - the coordinates of its ends
# any other variations (colors, labels...) are for human readability, and will be disregarded.

import geopandas as gpd
from shapely.geometry import Point, LineString

