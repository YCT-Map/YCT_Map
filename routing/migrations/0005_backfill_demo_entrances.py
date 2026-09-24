import uuid

from django.db import migrations


NAMESPACE = uuid.UUID("40000000-0000-4000-8000-000000000002")


def backfill(apps, schema_editor):
    Location = apps.get_model("locations", "Location")
    Entrance = apps.get_model("locations", "Entrance")
    LocationNetworkAnchor = apps.get_model("routing", "LocationNetworkAnchor")
    EntranceNetworkAnchor = apps.get_model("routing", "EntranceNetworkAnchor")

    anchors = LocationNetworkAnchor.objects.select_related("location").all()
    for legacy_anchor in anchors:
        location = legacy_anchor.location
        if location.entrance_latitude is None or location.entrance_longitude is None:
            continue
        entrance_id = uuid.uuid5(NAMESPACE, f"entrance:{location.id}")
        entrance, _ = Entrance.objects.update_or_create(
            id=entrance_id,
            defaults={
                "location_id": location.id,
                "name": f"{location.name} — Primary Entrance",
                "entrance_type": "MAIN",
                "latitude": location.entrance_latitude,
                "longitude": location.entrance_longitude,
                "is_primary": True,
                "is_active": True,
                "verification_state": location.verification_state,
            },
        )
        EntranceNetworkAnchor.objects.update_or_create(
            entrance_id=entrance.id,
            defaults={
                "node_id": legacy_anchor.node_id,
                "verification_state": legacy_anchor.verification_state,
                "is_active": legacy_anchor.is_active,
            },
        )


def reverse_backfill(apps, schema_editor):
    Entrance = apps.get_model("locations", "Entrance")
    ids = [uuid.uuid5(NAMESPACE, f"entrance:{location_id}") for location_id in Entrance.objects.values_list("location_id", flat=True)]
    Entrance.objects.filter(id__in=ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("locations", "0004_entrance_floor_internalplace_internalplacealias_and_more"),
        ("routing", "0004_entrancenetworkanchor"),
    ]

    operations = [migrations.RunPython(backfill, reverse_backfill)]
