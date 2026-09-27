"""Remove approved development records before production-candidate deployment."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from contributions.models import Contribution
from locations.models import InternalPlace, Location


DEMO_LOCATION_IDS = (
    "10000000-0000-4000-8000-000000000001",
    "10000000-0000-4000-8000-000000000002",
    "10000000-0000-4000-8000-000000000003",
    "10000000-0000-4000-8000-000000000004",
    "10000000-0000-4000-8000-000000000005",
    "10000000-0000-4000-8000-000000000006",
)
TEST_LOCATION_IDS = ("ea4fb789-35b5-45bc-bbe8-3ae4dace6fdc",)
RETAINED_LOCATION_NAMES = ("New Building", "Sports Complex")


class Command(BaseCommand):
    help = (
        "Dry-run or apply the owner-approved pre-deployment removal of known "
        "DEMO/test campus records. The operational routing graph is never deleted."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Commit the cleanup. Without this flag all changes are rolled back.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        all_target_ids = DEMO_LOCATION_IDS + TEST_LOCATION_IDS

        with transaction.atomic():
            retained = {
                item.name: item
                for item in Location.objects.filter(name__in=RETAINED_LOCATION_NAMES)
            }
            missing_retained = sorted(set(RETAINED_LOCATION_NAMES) - set(retained))
            if missing_retained:
                raise CommandError(
                    "Required retained Locations are missing: " + ", ".join(missing_retained)
                )

            targets = list(Location.objects.filter(pk__in=all_target_ids).order_by("name"))
            library = next((item for item in targets if str(item.pk) == DEMO_LOCATION_IDS[1]), None)

            contribution_count = 0
            if library:
                contribution_count = Contribution.objects.filter(
                    target_location=library
                ).count()

            self.stdout.write("Pre-deployment campus-data cleanup")
            self.stdout.write(f"Mode: {'APPLY' if apply_changes else 'DRY RUN'}")
            self.stdout.write(
                "Retaining: " + ", ".join(sorted(retained)) + " (UNVERIFIED)"
            )
            self.stdout.write(f"Locations selected for removal: {len(targets)}")
            for location in targets:
                self.stdout.write(
                    f"- {location.name} ({location.pk}): "
                    f"{location.entrances.count()} entrance(s), "
                    f"{location.floors.count()} floor(s), "
                    f"{location.internal_places.count()} internal place(s)"
                )
            self.stdout.write(
                f"Disposable DEMO Library contribution records selected: {contribution_count}"
            )

            sports = retained["Sports Complex"]
            demo_sports_entrances = sports.entrances.filter(
                verification_state=Location.VerificationState.DEMO
            )
            self.stdout.write(
                "Sports Complex entrances changing DEMO -> UNVERIFIED: "
                f"{demo_sports_entrances.count()}"
            )

            # Floors protect InternalPlaces. Remove approved test content explicitly
            # before deleting its parent Location tree.
            InternalPlace.objects.filter(location__in=targets).delete()
            Contribution.objects.filter(target_location=library).delete() if library else None
            Location.objects.filter(pk__in=all_target_ids).delete()
            demo_sports_entrances.update(
                verification_state=Location.VerificationState.UNVERIFIED
            )

            for location in retained.values():
                if location.verification_state != Location.VerificationState.UNVERIFIED:
                    location.verification_state = Location.VerificationState.UNVERIFIED
                    location.save(update_fields=("verification_state", "updated_at"))

            if not apply_changes:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("DRY RUN complete; all changes rolled back."))
            else:
                self.stdout.write(self.style.SUCCESS("Cleanup applied successfully."))
