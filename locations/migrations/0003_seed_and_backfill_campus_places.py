from django.db import migrations


CATEGORIES = (
    ("academic", "Academic", 10, "building"),
    ("administration", "Administration", 20, "office"),
    ("halls-events", "Halls & Events", 30, ""),
    ("food-snacks", "Food & Snacks", 40, "food"),
    ("sports-recreation", "Sports & Recreation", 50, ""),
    ("medical", "Medical", 60, "health"),
    ("library-study", "Library & Study", 70, "library"),
    ("student-services", "Student Services", 80, ""),
    ("security", "Security", 90, ""),
    ("accommodation", "Accommodation", 100, "hostel"),
    ("transport-gates", "Transport & Gates", 110, ""),
    ("other", "Other", 120, ""),
)

LEGACY_CATEGORY_MAP = {
    "building": "academic",
    "office": "administration",
    "food": "food-snacks",
    "health": "medical",
    "hostel": "accommodation",
    "library": "library-study",
}

PLACE_TYPE_MAP = {
    "building": "BUILDING",
    "office": "BUILDING",
    "food": "FACILITY",
    "health": "BUILDING",
    "hostel": "BUILDING",
    "library": "BUILDING",
}


def seed_and_backfill(apps, schema_editor):
    Category = apps.get_model("locations", "Category")
    Location = apps.get_model("locations", "Location")

    for slug, name, display_order, legacy_filter in CATEGORIES:
        Category.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "display_order": display_order,
                "legacy_filter": legacy_filter,
                "is_active": True,
            },
        )

    categories = {item.slug: item for item in Category.objects.all()}
    for location in Location.objects.all():
        location.representative_latitude = location.entrance_latitude
        location.representative_longitude = location.entrance_longitude
        location.publication_status = "PUBLISHED" if location.is_active else "ARCHIVED"
        location.place_type = PLACE_TYPE_MAP.get(location.category, "OTHER")
        location.save(
            update_fields=(
                "representative_latitude",
                "representative_longitude",
                "publication_status",
                "place_type",
            )
        )
        category_slug = LEGACY_CATEGORY_MAP.get(location.category)
        if category_slug:
            location.categories.add(categories[category_slug])


def reverse_backfill(apps, schema_editor):
    Category = apps.get_model("locations", "Category")
    Location = apps.get_model("locations", "Location")
    for location in Location.objects.all():
        location.categories.clear()
    Category.objects.filter(slug__in=[row[0] for row in CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [("locations", "0002_campus_place_foundation")]

    operations = [migrations.RunPython(seed_and_backfill, reverse_backfill)]
