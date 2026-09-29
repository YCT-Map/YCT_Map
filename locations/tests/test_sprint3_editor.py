from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from contributions.models import Contribution, ContributionResolution
from locations.forms import EntranceForm, InternalPlaceAliasFormSet, InternalPlaceForm, LocationForm
from locations.models import Entrance, Floor, InternalPlace, Location
from routing.editor_forms import WalkableNodeForm, WalkableSegmentForm
from routing.editor_services import split_segment
from routing.models import SourceType, VerificationState, WalkableNode, WalkableSegment


class SprintThreeEditorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user("sprint3-editor", password="test-password-42")
        cls.editor.groups.add(Group.objects.get(name="Editor"))

    def setUp(self):
        self.client.force_login(self.editor)

    def test_place_form_checkbox_contract_and_field_map(self):
        response = self.client.get(reverse("editor:place-create"))
        self.assertContains(response, 'id="place-map"')
        self.assertContains(response, 'id="id_representative_latitude"')
        self.assertContains(response, 'id="id_representative_longitude"')
        self.assertContains(response, "editor-place-map.js")
        self.assertContains(response, 'type="checkbox"')
        self.assertContains(response, 'name="is_checkpoint"')
        self.assertContains(response, "Show as map checkpoint")
        self.assertContains(response, "Emphasize this place as a prominent wayfinding landmark.")

    def test_primary_entrance_overwrite_requires_confirmation(self):
        location = Location.objects.create(name="Test place", category=Location.Category.BUILDING)
        Entrance.objects.create(location=location, name="Existing", entrance_type=Entrance.Type.MAIN,
            latitude="6.518000", longitude="3.374000", is_primary=True, is_active=True,
            verification_state=Location.VerificationState.UNVERIFIED)
        form = LocationForm({"name": "Test place", "description": "", "place_type": Location.PlaceType.BUILDING,
            "publication_status": Location.PublicationStatus.DRAFT, "representative_latitude": "6.518100",
            "representative_longitude": "3.374100", "capture_primary_entrance": "on"}, instance=location)
        self.assertFalse(form.is_valid())
        self.assertIn("Confirm before replacing", str(form.non_field_errors()))

    def place_payload(self, location, **overrides):
        values = {"name": location.name, "description": location.description,
            "place_type": location.place_type, "publication_status": location.publication_status,
            "aliases-TOTAL_FORMS": "0", "aliases-INITIAL_FORMS": "0",
            "aliases-MIN_NUM_FORMS": "0", "aliases-MAX_NUM_FORMS": "1000"}
        values.update(overrides); return values

    def test_combined_capture_requires_confirmation_then_decouples_points(self):
        location = Location.objects.create(name="Sports Complex", category=Location.Category.BUILDING)
        gate = Entrance.objects.create(location=location, name="Gate 1", entrance_type=Entrance.Type.MAIN,
            latitude="6.518000", longitude="3.374000", is_primary=True, is_active=True,
            verification_state=Location.VerificationState.UNVERIFIED)
        url = reverse("editor:place-detail", args=(location.id,))
        rejected = self.client.post(url, self.place_payload(location, representative_latitude="6.518200",
            representative_longitude="3.374200", capture_primary_entrance="on"))
        self.assertEqual(rejected.status_code, 200)
        gate.refresh_from_db(); location.refresh_from_db()
        self.assertEqual(str(gate.latitude), "6.518000"); self.assertIsNone(location.representative_latitude)
        accepted = self.client.post(url, self.place_payload(location, representative_latitude="6.518200",
            representative_longitude="3.374200", capture_primary_entrance="on", confirm_primary_overwrite="on"))
        self.assertEqual(accepted.status_code, 302)
        gate.refresh_from_db(); location.refresh_from_db()
        self.assertEqual(str(gate.latitude), "6.518200")
        moved = self.client.post(url, self.place_payload(location, representative_latitude="6.518300",
            representative_longitude="3.374300"))
        self.assertEqual(moved.status_code, 302)
        gate.refresh_from_db(); location.refresh_from_db()
        self.assertEqual(str(location.representative_latitude), "6.518300")
        self.assertEqual(str(gate.latitude), "6.518200")

    def test_publication_validation_and_routing_unavailable_are_normal_form_states(self):
        location = Location.objects.create(name="Publish QA", category=Location.Category.BUILDING)
        url = reverse("editor:place-detail", args=(location.id,))
        invalid = self.client.post(url, self.place_payload(location, publication_status=Location.PublicationStatus.PUBLISHED))
        self.assertEqual(invalid.status_code, 200)
        self.assertContains(invalid, "representative point is required")
        location.refresh_from_db(); self.assertEqual(location.publication_status, Location.PublicationStatus.DRAFT)
        valid = self.client.post(url, self.place_payload(location, publication_status=Location.PublicationStatus.PUBLISHED,
            representative_latitude="6.518200", representative_longitude="3.374200"))
        self.assertEqual(valid.status_code, 302)
        location.refresh_from_db(); self.assertEqual(location.publication_status, Location.PublicationStatus.PUBLISHED)
        detail = self.client.get(url)
        self.assertEqual(detail.status_code, 200); self.assertContains(detail, "Directions unavailable")

    def test_direct_invalid_reactivation_is_reported_without_crash(self):
        location = Location.objects.create(name="Archived incomplete", category=Location.Category.BUILDING,
            publication_status=Location.PublicationStatus.ARCHIVED)
        response = self.client.post(reverse("editor:place-reactivate", args=(location.id,)),
                                    {"publication_status": Location.PublicationStatus.PUBLISHED}, follow=True)
        self.assertEqual(response.status_code, 200); self.assertContains(response, "representative point is required")
        location.refresh_from_db(); self.assertEqual(location.publication_status, Location.PublicationStatus.ARCHIVED)

    def test_verification_is_not_editable_before_evidence_workflow(self):
        self.assertNotIn("verification_state", EntranceForm().fields)
        self.assertNotIn("verification_state", InternalPlaceForm().fields)

    def test_internal_alias_duplicates_are_normal_form_errors(self):
        location = Location.objects.create(name="Alias building", category=Location.Category.BUILDING)
        internal = InternalPlace(location=location, name="Room", internal_type=InternalPlace.Type.OTHER)
        formset = InternalPlaceAliasFormSet({"aliases-TOTAL_FORMS": "2", "aliases-INITIAL_FORMS": "0",
            "aliases-MIN_NUM_FORMS": "0", "aliases-MAX_NUM_FORMS": "1000",
            "aliases-0-name": "QA Lab", "aliases-0-alias_kind": "OTHER",
            "aliases-1-name": " qa lab ", "aliases-1-alias_kind": "OTHER"}, instance=internal, prefix="aliases")
        self.assertFalse(formset.is_valid()); self.assertIn("already used", str(formset.errors))

    def test_multiple_resolution_actions_and_approval_boundary(self):
        contribution = Contribution.objects.create(request_id="9f83aeca-83cb-4cef-9158-9ea681898ad7",
            status=Contribution.Status.APPROVED, contribution_type=Contribution.Type.OTHER,
            description="Review this map information")
        for note in ("Reviewed source", "Confirmed no change"):
            item = ContributionResolution(contribution=contribution, action=ContributionResolution.Action.NO_CHANGE,
                                          note=note, resolved_by=self.editor)
            item.full_clean(); item.save()
        self.assertEqual(contribution.resolutions.count(), 2)
        contribution.status = Contribution.Status.PENDING
        invalid = ContributionResolution(contribution=contribution, action=ContributionResolution.Action.NO_CHANGE,
                                         note="Too early")
        with self.assertRaises(ValidationError): invalid.full_clean()

    def test_resolution_and_path_editor_pages_render(self):
        contribution = Contribution.objects.create(request_id="18891677-3797-48e3-a3e5-da25a4d78e1e",
            status=Contribution.Status.APPROVED, contribution_type=Contribution.Type.OTHER,
            description="Approved information requiring explicit resolution")
        self.assertEqual(self.client.get(reverse("editor:contribution-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("editor:contribution-detail", args=(contribution.id,))).status_code, 200)
        self.assertEqual(self.client.get(reverse("editor:path-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("editor:node-create")).status_code, 200)
        self.assertEqual(self.client.get(reverse("editor:segment-create")).status_code, 200)

    def test_connected_node_cannot_be_dragged(self):
        first = self.node("A", 3.3740, 6.5180)
        second = self.node("B", 3.3742, 6.5180)
        self.segment(first, second)
        form = WalkableNodeForm({"label": "A", "longitude": "3.375000", "latitude": "6.518000", "is_active": "on"},
                                instance=first, locked=True)
        self.assertFalse(form.is_valid())
        self.assertIn("Connected nodes cannot be moved", str(form.non_field_errors()))

    def test_segment_form_serializes_simple_and_bent_linestring_and_round_trips(self):
        first = self.node("QA Node A", 3.3740, 6.5180); second = self.node("QA Node B", 3.3744, 6.5180)
        for coordinates in (
            [[3.3740, 6.5180], [3.3744, 6.5180]],
            [[3.3740, 6.5180], [3.3742, 6.5181], [3.3744, 6.5180]],
        ):
            form = WalkableSegmentForm({"label": "Segment QA Nodes", "start_node": first.id,
                "end_node": second.id, "geometry": {"type": "LineString", "coordinates": coordinates},
                "is_bidirectional": "on", "is_active": "on"})
            self.assertTrue(form.is_valid(), form.errors)
            segment = form.save(); self.assertGreater(segment.distance_metres, 0)
            reopened = WalkableSegmentForm(instance=segment)
            self.assertEqual(reopened.initial["geometry"], segment.geometry)
            segment.delete()
        mismatch = WalkableSegmentForm({"label": "Mismatch", "start_node": first.id, "end_node": second.id,
            "geometry": {"type": "LineString", "coordinates": [[3.375, 6.519], [3.3744, 6.5180]]},
            "is_active": "on"})
        self.assertFalse(mismatch.is_valid()); self.assertIn("endpoints must match", str(mismatch.errors))

    def test_metadata_edit_preserves_existing_segment_provenance_and_verification(self):
        first = self.node("A", 3.3740, 6.5180); second = self.node("B", 3.3744, 6.5180)
        segment = self.segment(first, second)
        segment.source_type = SourceType.OSM; segment.source_reference = "way/123";
        segment.verification_state = VerificationState.FIELD_VERIFIED; segment.save()
        form = WalkableSegmentForm({"label": "Renamed", "start_node": first.id, "end_node": second.id,
            "geometry": segment.geometry, "is_bidirectional": "on", "is_active": "on"}, instance=segment)
        self.assertTrue(form.is_valid(), form.errors); updated = form.save()
        self.assertEqual(updated.source_type, SourceType.OSM); self.assertEqual(updated.source_reference, "way/123")
        self.assertEqual(updated.verification_state, VerificationState.FIELD_VERIFIED)

    def test_explicit_segment_split_is_transactional_and_history_preserving(self):
        first = self.node("A", 3.3740, 6.5180)
        second = self.node("B", 3.3744, 6.5180)
        original = self.segment(first, second)
        node, left, right = split_segment(original, (3.3742, 6.5180), self.editor)
        original.refresh_from_db()
        self.assertFalse(original.is_active)
        self.assertEqual((left.end_node, right.start_node), (node, node))
        self.assertEqual(left.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(left.source_reference, f"split:{original.id}")
        self.assertEqual(WalkableSegment.objects.filter(is_active=True).count(), 2)

    @staticmethod
    def node(label, longitude, latitude):
        return WalkableNode.objects.create(label=label, longitude=longitude, latitude=latitude,
            verification_state=VerificationState.UNVERIFIED, source_type=SourceType.MANUAL)

    @staticmethod
    def segment(start, end):
        item = WalkableSegment(start_node=start, end_node=end, geometry={"type": "LineString", "coordinates": [
            [float(start.longitude), float(start.latitude)], [float(end.longitude), float(end.latitude)]]},
            verification_state=VerificationState.UNVERIFIED, source_type=SourceType.MANUAL)
        item.full_clean(); item.save(); return item
