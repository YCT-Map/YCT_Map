# Generated for YCT Map Phase 1 Sprint 001.

import uuid

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Location",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=160)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("building", "Buildings"),
                            ("office", "Offices"),
                            ("food", "Food"),
                            ("health", "Health"),
                            ("hostel", "Hostels"),
                            ("library", "Libraries"),
                        ],
                        max_length=24,
                    ),
                ),
                ("description", models.CharField(blank=True, max_length=280)),
                (
                    "entrance_latitude",
                    models.DecimalField(
                        decimal_places=6,
                        max_digits=9,
                        validators=[
                            django.core.validators.MinValueValidator(-90),
                            django.core.validators.MaxValueValidator(90),
                        ],
                    ),
                ),
                (
                    "entrance_longitude",
                    models.DecimalField(
                        decimal_places=6,
                        max_digits=9,
                        validators=[
                            django.core.validators.MinValueValidator(-180),
                            django.core.validators.MaxValueValidator(180),
                        ],
                    ),
                ),
                (
                    "verification_state",
                    models.CharField(
                        choices=[
                            ("DEMO", "Demo"),
                            ("UNVERIFIED", "Unverified"),
                            ("FIELD_VERIFIED", "Field verified"),
                        ],
                        default="UNVERIFIED",
                        max_length=24,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="LocationAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                (
                    "location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="aliases",
                        to="locations.location",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "constraints": [
                    models.UniqueConstraint(fields=("location", "name"), name="unique_location_alias")
                ],
            },
        ),
    ]
