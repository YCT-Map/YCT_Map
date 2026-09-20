"""Campus-place models shared by the public map and trusted editor."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower


class Category(models.Model):
    """Controlled functional discovery category for outdoor places."""

    slug = models.SlugField(max_length=48, primary_key=True)
    name = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    legacy_filter = models.CharField(max_length=24, blank=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Location(models.Model):
    class Category(models.TextChoices):
        """Legacy public-filter values retained for Phase 1–3 compatibility."""

        BUILDING = "building", "Buildings"
        OFFICE = "office", "Offices"
        FOOD = "food", "Food"
        HEALTH = "health", "Health"
        HOSTEL = "hostel", "Hostels"
        LIBRARY = "library", "Libraries"

    class PlaceType(models.TextChoices):
        BUILDING = "BUILDING", "Building"
        FACILITY = "FACILITY", "Facility"
        CAMPUS_AREA = "CAMPUS_AREA", "Campus area"
        GATE = "GATE", "Gate"
        FIELD = "FIELD", "Field"
        RECREATION_AREA = "RECREATION_AREA", "Recreation area"
        OTHER = "OTHER", "Other"

    class PublicationStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    class VerificationState(models.TextChoices):
        DEMO = "DEMO", "Demo"
        UNVERIFIED = "UNVERIFIED", "Unverified"
        FIELD_VERIFIED = "FIELD_VERIFIED", "Field verified"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    # Compatibility-only fields retained through Sprint 001.
    category = models.CharField(max_length=24, choices=Category.choices, blank=True, default="")
    entrance_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        null=True,
        blank=True,
    )
    entrance_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        null=True,
        blank=True,
    )
    description = models.CharField(max_length=280, blank=True)
    place_type = models.CharField(max_length=24, choices=PlaceType.choices, default=PlaceType.OTHER)
    categories = models.ManyToManyField("locations.Category", related_name="locations", blank=True)
    publication_status = models.CharField(
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
    )
    representative_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        null=True,
        blank=True,
    )
    representative_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        null=True,
        blank=True,
    )
    verification_state = models.CharField(
        max_length=24,
        choices=VerificationState.choices,
        default=VerificationState.UNVERIFIED,
    )
    # Retained as a compatibility flag while callers migrate to publication_status.
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_locations",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_locations",
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        self.description = self.description.strip()
        if not self.name:
            raise ValidationError({"name": "Enter a place name."})
        if (self.representative_latitude is None) != (self.representative_longitude is None):
            raise ValidationError({"representative_latitude": "Both representative coordinates are required."})
        if self.publication_status == self.PublicationStatus.PUBLISHED:
            if self.representative_latitude is None or self.representative_longitude is None:
                raise ValidationError({"publication_status": "A representative point is required before publication."})

    @property
    def has_representative_point(self):
        return self.representative_latitude is not None and self.representative_longitude is not None

    def __str__(self):
        return self.name


class LocationAlias(models.Model):
    class Kind(models.TextChoices):
        COMMON_NAME = "COMMON_NAME", "Common name"
        ABBREVIATION = "ABBREVIATION", "Abbreviation"
        CODE = "CODE", "Code"
        ALTERNATE_SPELLING = "ALTERNATE_SPELLING", "Alternate spelling"
        OTHER = "OTHER", "Other"

    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="aliases")
    name = models.CharField(max_length=160)
    alias_kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.OTHER)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "location",
                name="unique_location_alias_case_insensitive",
            )
        ]

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "Enter an alias."})
        if not self.location_id or self.location._state.adding:
            return
        duplicate = LocationAlias.objects.filter(location_id=self.location_id, name__iexact=self.name)
        if self.pk:
            duplicate = duplicate.exclude(pk=self.pk)
        if duplicate.exists():
            raise ValidationError({"name": "This alias is already used for this place."})

    def __str__(self):
        return self.name
