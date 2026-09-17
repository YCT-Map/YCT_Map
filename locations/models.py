"""Minimal Phase 1 destination models."""

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Location(models.Model):
    class Category(models.TextChoices):
        BUILDING = "building", "Buildings"
        OFFICE = "office", "Offices"
        FOOD = "food", "Food"
        HEALTH = "health", "Health"
        HOSTEL = "hostel", "Hostels"
        LIBRARY = "library", "Libraries"

    class VerificationState(models.TextChoices):
        DEMO = "DEMO", "Demo"
        UNVERIFIED = "UNVERIFIED", "Unverified"
        FIELD_VERIFIED = "FIELD_VERIFIED", "Field verified"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=24, choices=Category.choices)
    description = models.CharField(max_length=280, blank=True)
    entrance_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    entrance_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    verification_state = models.CharField(
        max_length=24,
        choices=VerificationState.choices,
        default=VerificationState.UNVERIFIED,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LocationAlias(models.Model):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="aliases",
    )
    name = models.CharField(max_length=160)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["location", "name"],
                name="unique_location_alias",
            )
        ]

    def __str__(self):
        return self.name
