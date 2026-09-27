from django.db import migrations


DEMO_LOCATION_IDS = (
    "10000000-0000-4000-8000-000000000001",
    "10000000-0000-4000-8000-000000000002",
    "10000000-0000-4000-8000-000000000003",
    "10000000-0000-4000-8000-000000000004",
    "10000000-0000-4000-8000-000000000005",
    "10000000-0000-4000-8000-000000000006",
)


def remove_development_demo_locations(apps, schema_editor):
    Location = apps.get_model("locations", "Location")
    InternalPlace = apps.get_model("locations", "InternalPlace")
    Contribution = apps.get_model("contributions", "Contribution")

    targets = Location.objects.filter(
        pk__in=DEMO_LOCATION_IDS,
        verification_state="DEMO",
    )
    InternalPlace.objects.filter(location__in=targets).delete()
    Contribution.objects.filter(target_location__in=targets).delete()
    targets.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("locations", "0004_entrance_floor_internalplace_internalplacealias_and_more"),
        ("contributions", "0002_alter_contribution_options_contributionresolution"),
        ("routing", "0009_entrancenetworkanchor_connector_geometry"),
    ]

    operations = [
        migrations.RunPython(remove_development_demo_locations, migrations.RunPython.noop),
    ]
