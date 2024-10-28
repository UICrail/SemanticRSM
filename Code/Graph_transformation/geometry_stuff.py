# Purpose of this module is to infer topology characteristics from geometric data.
# Topology can be set up from schematic or geographic representations of the network with low risk of error.
import itertools

from pyproj import Transformer
from rdflib import URIRef
from rdflib.namespace import RDF
from shapely.geometry import Point, LineString

from Namespaces import RSM_TOPOLOGY, GEOSPARQL

NAVIGABILITY_ANGULAR_THRESHOLD = 75  # degrees. Used for detecting the heel side of a switch on a schematic representation.

# Coordinate transformation. Note that the order (x, then y, or longitude, then latitude) is kept:
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3034", always_xy=True)


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


def find_nearest_linear_elements(lonlat: tuple[float, float], graph, count: int = 1) -> dict[URIRef:float]:
    """

    :param lonlat: longitude and latitude, decimal degrees (WGS84)
    :param graph: graph comprising linear elements and ports
    :param count: max number of linear elements to be returned
    :return: dict with <count> items, key = URIRef of linear element, value = projected distance from coords to element
    """

    # Transform input coordinates
    easting, northing = transformer.transform(*lonlat)
    point = Point(easting, northing)
    distances = {}

    for s, p, o in graph.triples((None, RDF.type, URIRef("http://cdm.ovh/rsm/topology/topology#LinearElement"))):
        ports = list(graph.objects(s, URIRef("http://cdm.ovh/rsm/topology/topology#hasPort")))

        if len(ports) == 2:
            port_coords = []
            for port in ports:
                wkt_literal = graph.value(port, URIRef("http://www.opengis.net/ont/geosparql#asWKT"))
                if wkt_literal:
                    lon, lat = wkt_point_to_lon_lat(wkt_literal)
                    easting, northing = transformer.transform(lon, lat)
                    port_coords.append((easting, northing))

            if len(port_coords) == 2:
                start_easting, start_northing = port_coords[0]
                end_easting, end_northing = port_coords[1]

                # Create a LineString for the segment
                line = LineString([(start_easting, start_northing), (end_easting, end_northing)])

                # Calculate projected distance from point to the line segment
                distance = point.distance(line)
                distances[s] = distance

    # Return the nearest 'count' elements
    nearest_elements = dict(sorted(distances.items(), key=lambda item: item[1]))
    if len(nearest_elements) > count:
        count_nearest_elements = {k: nearest_elements[k] for k in itertools.islice(nearest_elements, count)}
        return count_nearest_elements
    return nearest_elements


def find_nearest_ports(coords: tuple[float, float], graph, net_element, count: int = 1) -> dict[URIRef:float]:
    """
    In this version, only linear net elements are considered.
    :param coords: easting and northing
    :param graph: containing linear elements and their ports, with coordinates as WKT literals
    :param net_element: the net element considered
    :param count: max number of ports to be returned (cannot exceed 2 if element is a linear one)
    :return: dict[URIRef:float] where URIRef refers to the port, and float is the value of the distance
    """

    point = Point(coords)
    distances = {}

    # Iterate over ports of the given net element
    ports = list(graph.objects(net_element, RSM_TOPOLOGY.hasPort))
    for port in ports:
        wkt_literal = graph.value(port, GEOSPARQL.asWKT)
        if wkt_literal:
            lon, lat = wkt_point_to_lon_lat(wkt_literal)
            easting, northing = transformer.transform(lon, lat)

            port_point = Point(easting, northing)
            distance = point.distance(port_point)
            # TODO: the above does not look right. Maybe an issue with coordinate order, again...
            distances[port] = distance

    # Return the nearest 'count' ports
    nearest_ports = dict(sorted(distances.items(), key=lambda item: item[1]))
    if len(nearest_ports) > count:
        count_nearest_ports = {k: nearest_ports[k] for k in itertools.islice(nearest_ports, count)}
        return count_nearest_ports
    return nearest_ports


def wkt_point_to_lon_lat(wkt_literal: str) -> tuple[float, float]:
    """
    Turn WKT point into longitude and latitude.
    :param wkt_literal: expected is a string like 'POINT(2.345678 45.1234)'; as per OGC standards, longitude first!
    :return: longitude and latitude, in decimal degrees (WGS84)
    """
    coords = wkt_literal.split("(")[1].split(")")[0].split()
    lon, lat = map(float, coords)
    return lon, lat


if __name__ == "__main__":
    coords = 'POINT(2.345678 45.1234)'
    lon, lat = wkt_point_to_lon_lat(coords)
    print(lon, lat)
