from decimal import Decimal
from django.test import TestCase

from routing.labels import (
    classify_route_verification,
    clean_node_label,
    clean_segment_label,
    integer_to_segment_code,
    is_valid_node_label,
    is_valid_segment_label,
    next_node_label,
    next_segment_label,
    segment_code_to_integer,
)
from routing.models import VerificationState, WalkableNode, WalkableSegment


class LabelHelperTests(TestCase):
    def test_integer_to_segment_code_conversion(self):
        cases = {
            1: "A",
            2: "B",
            26: "Z",
            27: "AA",
            28: "AB",
            52: "AZ",
            53: "BA",
            702: "ZZ",
            703: "AAA",
        }
        for n, expected in cases.items():
            self.assertEqual(integer_to_segment_code(n), expected)
            self.assertEqual(segment_code_to_integer(expected), n)

    def test_segment_code_round_trip(self):
        for n in range(1, 1000):
            code = integer_to_segment_code(n)
            self.assertEqual(segment_code_to_integer(code), n)

    def test_invalid_segment_conversions(self):
        with self.assertRaises(ValueError):
            integer_to_segment_code(0)
        with self.assertRaises(ValueError):
            integer_to_segment_code(-5)
        with self.assertRaises(ValueError):
            segment_code_to_integer("")
        with self.assertRaises(ValueError):
            segment_code_to_integer("A1")

    def test_clean_node_label(self):
        self.assertEqual(clean_node_label("1"), "1")
        self.assertEqual(clean_node_label("Node 42"), "42")
        self.assertEqual(clean_node_label("NODE 7"), "7")
        self.assertEqual(clean_node_label("  99  "), "99")
        self.assertEqual(clean_node_label("osm_node_123"), "osm_node_123")
        self.assertTrue(is_valid_node_label("1"))
        self.assertTrue(is_valid_node_label("42"))
        self.assertFalse(is_valid_node_label("Node 1"))
        self.assertFalse(is_valid_node_label("0"))
        self.assertFalse(is_valid_node_label("-1"))

    def test_clean_segment_label(self):
        self.assertEqual(clean_segment_label("A"), "A")
        self.assertEqual(clean_segment_label("Segment B"), "B")
        self.assertEqual(clean_segment_label("SEGMENT AA"), "AA")
        self.assertEqual(clean_segment_label("  c  "), "C")
        self.assertEqual(clean_segment_label("osm_way_456"), "OSM_WAY_456")
        self.assertTrue(is_valid_segment_label("A"))
        self.assertTrue(is_valid_segment_label("ZZ"))
        self.assertFalse(is_valid_segment_label("Segment A"))
        self.assertFalse(is_valid_segment_label("A1"))
        self.assertFalse(is_valid_segment_label(""))

    def test_next_node_and_segment_label_allocation(self):
        # Empty DB:
        self.assertEqual(next_node_label(), "1")
        self.assertEqual(next_segment_label(), "A")

        # Create nodes and segments
        node1 = WalkableNode.objects.create(latitude=Decimal("6.5185"), longitude=Decimal("3.3742"), label="1")
        node2 = WalkableNode.objects.create(latitude=Decimal("6.5186"), longitude=Decimal("3.3743"), label="2")
        self.assertEqual(next_node_label(), "3")

        # Create segment with label "A"
        geom = {
            "type": "LineString",
            "coordinates": [[3.3742, 6.5185], [3.3743, 6.5186]],
        }
        WalkableSegment.objects.create(
            start_node=node1,
            end_node=node2,
            geometry=geom,
            label="A",
        )
        self.assertEqual(next_segment_label(), "B")

        # Handles non-numeric/non-alphabetic legacy gracefully:
        WalkableNode.objects.create(latitude=Decimal("6.5187"), longitude=Decimal("3.3744"), label="legacy-node")
        self.assertEqual(next_node_label(), "3")

    def test_classify_route_verification(self):
        self.assertEqual(
            classify_route_verification([VerificationState.FIELD_VERIFIED, VerificationState.FIELD_VERIFIED]),
            VerificationState.FIELD_VERIFIED,
        )
        self.assertEqual(
            classify_route_verification([VerificationState.DEMO, VerificationState.DEMO]),
            VerificationState.DEMO,
        )
        self.assertEqual(
            classify_route_verification([VerificationState.FIELD_VERIFIED, VerificationState.DEMO]),
            VerificationState.UNVERIFIED,
        )
        self.assertEqual(
            classify_route_verification([VerificationState.FIELD_VERIFIED, VerificationState.UNVERIFIED]),
            VerificationState.UNVERIFIED,
        )
        self.assertEqual(
            classify_route_verification([]),
            VerificationState.UNVERIFIED,
        )
