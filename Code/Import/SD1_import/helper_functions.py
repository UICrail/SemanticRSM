import datetime

import numpy
import numpy as np


def millimeters_to_meters(some_length_in_integer_mm: str) -> str:
    """
    From string expressing lengths in integer millimeter, to string expressing the same in meters (decimal notation)
    :param some_length_in_integer_mm:
    :return:
    """
    return some_length_in_integer_mm[:-3] + '.' + some_length_in_integer_mm[-3:]


def replace_strings(input_string: str, string_mapping: dict, reverse_mapping: bool = False) -> str:
    """
    Function to replace strings based on a given mapping dictionary.
    :param input_string: any string
    :param string_mapping: dictionary of terms, key = a term, value = its equivalent
    :param reverse_mapping: if False, the keys will be looked up in input_string and replaced by the corresp. value;
    if True, the values will be looked up in input_string and replaced by the keys
    :return a string which is a copy of the input string, but for all replacements
    """
    for original, replacement in string_mapping.items():
        input_string = input_string.replace((original if not reverse_mapping else replacement),
                                            (replacement if not reverse_mapping else original))
    return input_string


def rotate(some_list: list, shift: int) -> list:
    return some_list[shift:] + some_list[:shift]


def timestamp_from_date(yyyy_mm_dd: str) -> int:
    """returns number of seconds elapsed since 1/1/1970 00:00:00 UTC+0, as defined in IEEE Std 1003.1.
    :param yyyy_mm_dd: 'YYYY-MM-DD', assumed to be in UTC+0
    :return: integer number of seconds, conforming IfcTimeStamp definition"""
    # TODO: use explicit timezone info (in the present version, local timezone is assumed)
    year, month, day = [int(x) for x in yyyy_mm_dd.split('-')]
    this_date = datetime.datetime(year, month, day)
    return int(this_date.timestamp())


def utm_central_meridian(longitude: float) -> float:
    """position of central meridian of UTM/TimeZone encompassing the stated longitude,
    in the Northern hemisphere, at intermediate latitudes on the continent.
    The case of irregular time zones is not relevant there"""
    ZONE_WIDTH_DEGREES = 6.0
    return (longitude // ZONE_WIDTH_DEGREES) * ZONE_WIDTH_DEGREES + ZONE_WIDTH_DEGREES / 2.0


def grid_convergence(latitude: float, longitude: float) -> float:
    """returns angle between grid north (in a projected, cartesian coordinate system) and true north at some point.
    Assumes spherical (not: ellipsoidal, for simplicity) UTM projection.
    :param latitude: latitude of point in degrees
    :param longitude: longitude of point in degrees"""
    # longitude of central meridian of UTM zone
    longitude_of_central_meridian = utm_central_meridian(longitude)
    return numpy.arctan(numpy.tan(longitude - longitude_of_central_meridian) * numpy.sin(latitude))


def azimuth_to_direction(azimuth: float, longitude: float = None, latitude: float = None) -> float:
    """assuming that SD1 data provide a *grid* azimuth (0 degree points to grid North, increasing clockwise).
    Direction in IFC is however counted CCW, starting from X axis direction.
    If azimuth is with respect to true North, the longitude and latitude of the point where the azimuth is expressed
     is needed to calculate the direction, using grid_convergence (not implemented yet)."""
    return 90 - azimuth


def delta_x_delta_y(initial_direction: float, arc_length: float, arc_radius: float = 0) -> np.array:
    """In a cartesian coordinate system, assuming a circular arc of radius arc_radius (negative if turning clockwise),
    and an initial direction (positive counterclockwise from X axis), and an arc length (always positive), this
    function will return the X- and Y- projection of the chord.
    This function is valid for circular arcs and straight lines (where radius of curvature is 0 by convention)
    :param initial_direction: signed initial direction in degrees
    :param arc_length: arc length in meter (>0)
    :param arc_radius: signed arc radius in meter; special case: 0 means straight segment
    :return: X- and Y- projection of the chord"""
    assert arc_length > 0, "Arc length must be positive"
    initial_direction_rd = initial_direction * numpy.pi / 180
    if arc_radius == 0:
        delta_x = float(arc_length * numpy.cos(initial_direction_rd))
        delta_y = float(arc_length * numpy.sin(initial_direction_rd))
    else:
        arc_angle_rd = arc_length / arc_radius  # in radian
        chord_length = 2 * abs(arc_radius * numpy.sin(arc_angle_rd / 2))
        chord_angle = initial_direction_rd + arc_angle_rd / 2
        delta_x = float(chord_length * numpy.cos(chord_angle))
        delta_y = float(chord_length * numpy.sin(chord_angle))
    return np.array((delta_x, delta_y))


def arc_end_coords(start_coords: np.array, initial_direction: float, arc_length: float,
                   arc_radius: float = 0) -> np.array:
    """This function is valid for circular arcs and straight lines (where radius of curvature is 0 by convention)."""
    delta = delta_x_delta_y(initial_direction, arc_length, arc_radius)
    return start_coords + delta


if __name__ == '__main__':
    def test_convergence_angle():
        lat = 50.541454  # Scheibenberg (town)
        lon = 12.912986  # ditto
        print(grid_convergence(lat, lon))  # returns 0.447, apparently counted clockwise form true North in degrees


    def test_delta_x_delta_y():
        """see geometry drawing : file 240728...png"""
        initial_direction = 45
        arc_length = (2 * numpy.pi * 3.41) * 27.97 / 360
        arc_radius = -3.41
        print(delta_x_delta_y(initial_direction, arc_length, arc_radius))


    test_delta_x_delta_y()
