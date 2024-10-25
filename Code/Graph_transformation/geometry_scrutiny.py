# Purpose of this module is to infer topology characteristics from geometric data.
# Topology can be set up from schematic or geographic representations of the network with low risk of error.

NAVIGABILITY_ANGULAR_THRESHOLD = 30  # degrees


def deviation_angle(azimuth_1: float, azimuth_2: float) -> float:
    """
    Deviation angle at the junction between two linear elements.
    :param azimuth_1: of port X of element A at junction
    :param azimuth_2: of port Y of element B at junction
    :return: angle, in degrees, in [-180, 180] interval
    """
    dev = azimuth_1 - (azimuth_2 - 180)
    if dev > 180:
        dev -= 360
    elif dev < -180:
        dev += 360
    return dev


def possible_navigability(azimuth_1: float, azimuth_2: float,
                          small_angle: float = NAVIGABILITY_ANGULAR_THRESHOLD) -> bool:
    """
    Determines whether it is possible to navigate between linear elements basing on the azimuths of their connected
    extremities. Azimuths values are provided in degrees, in the range [-180, 180] (this is a pyproj setting).
    "Possibility" is provided when the azimuth difference, modulo 180 degrees, is "small".
    :param azimuth_1:
    :param azimuth_2:
    :param small_angle: 30° by default
    :return: True if navigability is possible, else False
    """
    abs_deviation = abs(deviation_angle(azimuth_1, azimuth_2))
    return abs_deviation < small_angle
