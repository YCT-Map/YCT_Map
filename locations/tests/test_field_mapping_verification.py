from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from locations.models import Entrance, Location


class PlaceEntranceVerificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user("field-editor", password="test-password-42")
        cls.editor.groups.add(Group.objects.get(name="Editor"))
        cls.verifier = get_user_model().objects.create_user("field-verifier", password="test-password-42")
        cls.verifier.user_permissions.add(*Permission.objects.filter(codename__in=(
            "change_location", "view_location", "change_entrance", "view_entrance",
            "grant_field_verified", "revoke_field_verified",
        )))

    def setUp(self):
        self.place = Location.objects.create(
            name="TEST — Field building", place_type=Location.PlaceType.BUILDING,
            publication_status=Location.PublicationStatus.PUBLISHED,
            representative_longitude=Decimal("3.374200"), representative_latitude=Decimal("6.518500"),
            verification_state=Location.VerificationState.UNVERIFIED, is_checkpoint=True, is_active=True,
        )
        self.entrance = Entrance.objects.create(
            location=self.place, name="Main entrance", longitude=Decimal("3.374210"),
            latitude=Decimal("6.518510"), verification_state=Location.VerificationState.UNVERIFIED,
        )

    def test_model_defaults_remain_unverified(self):
        place = Location(name="TEST — Default state", place_type=Location.PlaceType.BUILDING)
        entrance = Entrance(location=self.place, name="Secondary", longitude=Decimal("3.374220"),
                            latitude=Decimal("6.518520"))
        self.assertEqual(place.verification_state, Location.VerificationState.UNVERIFIED)
        self.assertEqual(entrance.verification_state, Location.VerificationState.UNVERIFIED)

    def test_verifier_grants_place_without_changing_publication_checkpoint_or_entrance(self):
        self.client.force_login(self.verifier)
        response = self.client.post(reverse("editor:place-verification", args=(self.place.pk,)), {
            "action": "grant", "reason": "Observed and checked on campus.",
        })
        self.assertRedirects(response, reverse("editor:place-detail", args=(self.place.pk,)))
        self.place.refresh_from_db(); self.entrance.refresh_from_db()
        self.assertEqual(self.place.verification_state, Location.VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.place.publication_status, Location.PublicationStatus.PUBLISHED)
        self.assertTrue(self.place.is_checkpoint)
        self.assertEqual(self.entrance.verification_state, Location.VerificationState.UNVERIFIED)

    def test_entrance_verification_is_independent_and_revocable(self):
        self.client.force_login(self.verifier)
        url = reverse("editor:entrance-verification", args=(self.place.pk, self.entrance.pk))
        self.client.post(url, {"action": "grant", "reason": "Doorway checked."})
        self.entrance.refresh_from_db(); self.place.refresh_from_db()
        self.assertEqual(self.entrance.verification_state, Location.VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.place.verification_state, Location.VerificationState.UNVERIFIED)
        self.client.post(url, {"action": "revoke", "reason": "Physical point needs recheck."})
        self.entrance.refresh_from_db()
        self.assertEqual(self.entrance.verification_state, Location.VerificationState.UNVERIFIED)

    def test_ordinary_editor_cannot_grant_verification(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse("editor:place-verification", args=(self.place.pk,)), {
            "action": "grant", "reason": "Not authorized.",
        })
        self.assertEqual(response.status_code, 403)
        self.place.refresh_from_db()
        self.assertEqual(self.place.verification_state, Location.VerificationState.UNVERIFIED)

    def test_reason_is_required_and_coordinate_edit_demotes_entrance(self):
        self.place.verification_state = Location.VerificationState.FIELD_VERIFIED
        self.place.save(update_fields=("verification_state",))
        self.entrance.verification_state = Location.VerificationState.FIELD_VERIFIED
        self.entrance.save(update_fields=("verification_state",))
        self.client.force_login(self.verifier)
        self.client.post(reverse("editor:place-verification", args=(self.place.pk,)), {
            "action": "revoke", "reason": "",
        })
        self.place.refresh_from_db()
        self.assertEqual(self.place.verification_state, Location.VerificationState.FIELD_VERIFIED)
        response = self.client.post(reverse("editor:entrance-edit", args=(self.place.pk, self.entrance.pk)), {
            "name": "Main entrance", "entrance_type": Entrance.Type.MAIN,
            "longitude": "3.374250", "latitude": "6.518550", "is_active": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.entrance.refresh_from_db()
        self.assertEqual(self.entrance.verification_state, Location.VerificationState.UNVERIFIED)

    def test_forms_expose_shared_capture_and_real_status(self):
        self.client.force_login(self.verifier)
        place = self.client.get(reverse("editor:place-detail", args=(self.place.pk,)))
        entrance = self.client.get(reverse("editor:entrance-edit", args=(self.place.pk, self.entrance.pk)))
        self.assertContains(place, "Mark place as field verified")
        self.assertContains(place, "data-campus-boundary-url")
        self.assertContains(entrance, 'id="capture-entrance-location"')
        self.assertContains(entrance, "Mark entrance as field verified")
        self.assertContains(entrance, "data-campus-boundary-url")
