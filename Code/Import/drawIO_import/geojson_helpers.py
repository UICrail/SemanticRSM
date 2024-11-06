import geojson
from fastkml.geometry import LineString
from pyproj import Transformer

CANVAS_ORIENTATION = -1  # if Y value increases when going down
# Coordinate reference systems
# ETRS89-extended / LCC Europe is the default projection
DEFAULT_PROJECTION = "EPSG:3034"
DEFAULT_CENTER_COORDS = 3536037.64, 4115023.91  # Easting, Northing; of EPSG 3034; somewhere off Norwegian coast
# WGS84
DEFAULT_GEO_REFERENCE = "EPSG:4326"
# coordinate transformer function, 3034 -> 4326
transformer = Transformer.from_crs(DEFAULT_PROJECTION, DEFAULT_GEO_REFERENCE, always_xy=True)


def convert_multiple_canvas_coords_to_lonlat(*coords: tuple[str | float, str | float]) -> \
        tuple[tuple[float, float], ...]:
    """
    Convert Cartesian coordinates on canvas to longitude and latitude.

    :param coords: array of coordinate pairs (X,Y) [, (X1, Y1)...] on some canvas
    :return: Tuple of longitude and latitude pairs.
    """
    return tuple(_convert_canvas_coords_to_lonlat(coord) for coord in coords)


def _convert_canvas_coords_to_lonlat(coord: tuple[str | float, str | float]) -> tuple[float, float]:
    """
    Convert a single coordinate pair from Cartesian (on canvas) to longitude and latitude.
    Note that the ordering conventions for coordinates differ...
    :param coord: Coordinate pair (X, Y) on Canvas
    :return: Converted coordinate pair (longitude, latitude)
    """
    result = transformer.transform(*_convert_canvas_coords_to_projection(coord))
    return result


def _convert_canvas_coords_to_projection(canvas_coord: tuple[str | float, str | float]) -> tuple[float, float]:
    result = float(canvas_coord[0]) + DEFAULT_CENTER_COORDS[0], \
             CANVAS_ORIENTATION * float(canvas_coord[1]) + DEFAULT_CENTER_COORDS[1]
    return result


def create_geojson_linestring(source: tuple[str | float, str | float], target: tuple[str | float, str | float],
                              *waypoints: tuple[str | float, str | float]) -> LineString:
    """
    Create a GeoJSON LineString from source, target, and optional waypoints.

    :param source: (X, Y) coordinate pair (on canvas) for the source.
    :param target: (X, Y) coordinate pair (on canvas) for the target.
    :param waypoints: Optional waypoints between source and target.
    :return: GeoJSON LineString object.
    """
    way_coords = (
        *convert_multiple_canvas_coords_to_lonlat(source),
        *convert_multiple_canvas_coords_to_lonlat(*waypoints),
        *convert_multiple_canvas_coords_to_lonlat(target)
    )
    result = geojson.LineString(way_coords)
    return result


def create_geojson_point(x: float | str, y: float | str) -> geojson.Point:
    """
    Create a GeoJSON point from Cartesian coordinates on canvas.

    :param x: X coordinate.
    :param y: Y coordinate.
    :return: GeoJSON Point object.
    """
    return geojson.Point(_convert_canvas_coords_to_lonlat((float(x), float(y))))


if __name__ == '__main__':
    print(_convert_canvas_coords_to_projection((0, 0)))
    print(_convert_canvas_coords_to_lonlat((0, 0)))
