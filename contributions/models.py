import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models

from locations.models import Location


class Contribution(models.Model):
    class Type(models.TextChoices):
        ADD_LOCATION = "ADD_LOCATION", "Add a missing place"
        CORRECT_LOCATION = "CORRECT_LOCATION", "Correct an existing place"
        REPORT_ACCESS_OR_PATH = "REPORT_ACCESS_OR_PATH", "Report an access or path issue"
        ADD_INFORMATION = "ADD_INFORMATION", "Add information about a place"
        OTHER = "OTHER", "Other map correction"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved for later editor action"
        REJECTED = "REJECTED", "Rejected"
        MERGED = "MERGED", "Merged as duplicate"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_id = models.UUIDField(unique=True, editable=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    contribution_type = models.CharField(max_length=32, choices=Type.choices)
    target_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name="contributions")
    proposed_name = models.CharField(max_length=160, blank=True)
    proposed_category = models.CharField(max_length=24, choices=Location.Category.choices, blank=True)
    description = models.TextField(max_length=1000, validators=[MaxLengthValidator(1000)])
    context = models.CharField(max_length=240, blank=True)
    proposed_latitude = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)])
    proposed_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)])
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="reviewed_contributions")
    moderator_note = models.TextField(max_length=1000, blank=True)
    merged_into = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="merged_duplicates")
    resolved_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL,
                                          related_name="resolved_contributions")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def clean(self):
        super().clean()
        self.description = self.description.strip()
        self.proposed_name = self.proposed_name.strip()
        self.context = self.context.strip()
        if not self.description:
            raise ValidationError({"description": "Describe the correction or addition."})
        if (self.proposed_latitude is None) != (self.proposed_longitude is None):
            raise ValidationError({"proposed_latitude": "Both coordinates are required for a proposed point."})
        if self.contribution_type == self.Type.ADD_LOCATION and not self.proposed_name:
            raise ValidationError({"proposed_name": "Enter the proposed place name."})
        if self.contribution_type in {self.Type.CORRECT_LOCATION, self.Type.ADD_INFORMATION} and not self.target_location:
            raise ValidationError({"target_location": "Choose the existing place this report concerns."})
        if self.status == self.Status.MERGED and not self.merged_into:
            raise ValidationError({"merged_into": "Select the contribution this duplicate was merged into."})
        if self.merged_into_id == self.id:
            raise ValidationError({"merged_into": "A contribution cannot be merged into itself."})

    def __str__(self):
        return f"{self.get_contribution_type_display()} — {self.id}"
