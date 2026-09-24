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


class AuditModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_%(class)ss", editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="updated_%(class)ss", editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Entrance(AuditModel):
    class Type(models.TextChoices):
        MAIN = "MAIN", "Main entrance"
        BUILDING = "BUILDING", "Building entrance"
        HALL = "HALL", "Hall entrance"
        BACK = "BACK", "Back entrance"
        SIDE = "SIDE", "Side entrance"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="entrances")
    name = models.CharField(max_length=160)
    entrance_type = models.CharField(max_length=16, choices=Type.choices, default=Type.OTHER)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    verification_state = models.CharField(
        max_length=24, choices=Location.VerificationState.choices, default=Location.VerificationState.UNVERIFIED,
    )

    class Meta:
        ordering = ["-is_primary", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["location"], condition=models.Q(is_primary=True, is_active=True),
                name="one_active_primary_entrance_per_location",
            )
        ]

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "Enter an entrance name."})
        if self.is_primary and not self.is_active:
            raise ValidationError({"is_primary": "A primary entrance must be active."})

    def __str__(self):
        return f"{self.location} — {self.name}"


class Floor(AuditModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="floors")
    level = models.SmallIntegerField()
    label = models.CharField(max_length=80)
    display_order = models.SmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "level", "label"]
        constraints = [models.UniqueConstraint(fields=["location", "level"], name="unique_floor_level_per_location")]

    def clean(self):
        super().clean()
        self.label = self.label.strip()
        if not self.label:
            raise ValidationError({"label": "Enter a floor label."})

    def __str__(self):
        return f"{self.location} — {self.label}"


class InternalPlace(AuditModel):
    class Type(models.TextChoices):
        CLASSROOM = "CLASSROOM", "Classroom"
        LECTURE_HALL = "LECTURE_HALL", "Lecture hall"
        EVENT_HALL = "EVENT_HALL", "Event hall"
        LABORATORY = "LABORATORY", "Laboratory"
        OFFICE = "OFFICE", "Office"
        DEPARTMENT = "DEPARTMENT", "Department"
        STUDIO = "STUDIO", "Studio"
        MEETING_ROOM = "MEETING_ROOM", "Meeting room"
        FOOD_SPOT = "FOOD_SPOT", "Internal food spot"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="internal_places")
    floor = models.ForeignKey(Floor, null=True, blank=True, on_delete=models.PROTECT, related_name="internal_places")
    name = models.CharField(max_length=160)
    internal_type = models.CharField(max_length=24, choices=Type.choices)
    room_code = models.CharField(max_length=80, blank=True)
    wing_section = models.CharField(max_length=120, blank=True)
    direction_note = models.CharField(max_length=500, blank=True)
    routing_entrance = models.ForeignKey(
        Entrance, null=True, blank=True, on_delete=models.PROTECT, related_name="internal_destinations",
    )
    publication_status = models.CharField(
        max_length=16, choices=Location.PublicationStatus.choices, default=Location.PublicationStatus.DRAFT,
    )
    verification_state = models.CharField(
        max_length=24, choices=Location.VerificationState.choices, default=Location.VerificationState.UNVERIFIED,
    )

    class Meta:
        ordering = ["location__name", "floor__display_order", "name"]

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        self.room_code = self.room_code.strip()
        self.wing_section = self.wing_section.strip()
        self.direction_note = self.direction_note.strip()
        if not self.name:
            raise ValidationError({"name": "Enter an internal place name."})
        if self.floor_id and self.floor.location_id != self.location_id:
            raise ValidationError({"floor": "The floor must belong to the same outdoor place."})
        if self.routing_entrance_id:
            if self.routing_entrance.location_id != self.location_id:
                raise ValidationError({"routing_entrance": "The entrance must belong to the same outdoor place."})
            if not self.routing_entrance.is_active:
                raise ValidationError({"routing_entrance": "Choose an active entrance."})
        if self.publication_status == Location.PublicationStatus.PUBLISHED:
            if self.location.publication_status != Location.PublicationStatus.PUBLISHED:
                raise ValidationError({"publication_status": "The parent outdoor place must be Published."})
            if not self.floor_id or not self.floor.is_active:
                raise ValidationError({"floor": "A Published internal place requires an active floor."})

    def __str__(self):
        return self.name


class InternalPlaceAlias(models.Model):
    internal_place = models.ForeignKey(InternalPlace, on_delete=models.CASCADE, related_name="aliases")
    name = models.CharField(max_length=160)
    alias_kind = models.CharField(max_length=24, choices=LocationAlias.Kind.choices, default=LocationAlias.Kind.OTHER)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"), "internal_place", name="unique_internal_alias_case_insensitive",
            )
        ]

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "Enter an alias."})
        if not self.internal_place_id or self.internal_place._state.adding:
            return
        duplicate = InternalPlaceAlias.objects.filter(
            internal_place_id=self.internal_place_id, name__iexact=self.name,
        )
        if self.pk:
            duplicate = duplicate.exclude(pk=self.pk)
        if duplicate.exists():
            raise ValidationError({"name": "This alias is already used for this internal place."})

    def __str__(self):
        return self.name
