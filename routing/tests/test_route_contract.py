from django.test import SimpleTestCase

from routing.route_contract import InvalidRouteGeometryError, route_geojson_geometry


class RouteCoordinateContractTests(SimpleTestCase):
    def test_yabatech_route_serializes_as_longitude_latitude(self):
        geometry = route_geojson_geometry(((3.37378, 6.51828), (3.37424, 6.51857)))

        self.assertEqual(geometry["type"], "LineString")
        self.assertEqual(geometry["coordinates"][0], [3.37378, 6.51828])
        self.assertEqual(geometry["coordinates"][-1], [3.37424, 6.51857])

    def test_reversed_yabatech_coordinate_is_rejected(self):
        with self.assertRaisesMessage(InvalidRouteGeometryError, "coordinate order may be invalid"):
            route_geojson_geometry(((6.51828, 3.37378), (6.51857, 3.37424)))

    def test_malformed_and_out_of_range_coordinates_are_rejected(self):
        for points in ((), ((3.37,),), ((181, 6.52),), ((float("nan"), 6.52),)):
            with self.subTest(points=points), self.assertRaises(InvalidRouteGeometryError):
                route_geojson_geometry(points)
