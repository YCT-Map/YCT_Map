import uuid
import hashlib
import json

from django.conf import settings

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from locations.models import Entrance, Location

from .geometry import coordinates, distance_metres, length_metres


class VerificationState(models.TextChoices):
    DEMO = "DEMO", "Demonstration data"
    UNVERIFIED = "UNVERIFIED", "Unverified"
    FIELD_VERIFIED = "FIELD_VERIFIED", "Field verified"


class SourceType(models.TextChoices):
    SYNTHETIC = "SYNTHETIC", "Synthetic fixture"
    OSM = "OSM", "OpenStreetMap"
    MANUAL = "MANUAL", "YCT Map manual"


class WalkableNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=120, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    latitude = models.DecimalField(max_digits=8, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    verification_state = models.CharField(max_length=20, choices=VerificationState.choices)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.MANUAL)
    source_reference = models.CharField(max_length=80, blank=True)
    source_version = models.PositiveIntegerField(null=True, blank=True)
    source_timestamp = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="created_walkable_nodes", editable=False)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="updated_walkable_nodes", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label or str(self.id)


class WalkableSegment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=120, blank=True)
    start_node = models.ForeignKey(WalkableNode, on_delete=models.PROTECT, related_name="outgoing_segments")
    end_node = models.ForeignKey(WalkableNode, on_delete=models.PROTECT, related_name="incoming_segments")
    geometry = models.JSONField()
    is_bidirectional = models.BooleanField(default=True)
    verification_state = models.CharField(max_length=20, choices=VerificationState.choices)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.MANUAL)
    source_reference = models.CharField(max_length=80, blank=True)
    source_version = models.PositiveIntegerField(null=True, blank=True)
    source_timestamp = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    geometry_revision = models.PositiveIntegerField(default=1, editable=False)
    geometry_fingerprint = models.CharField(max_length=64, blank=True, editable=False)
    derived_from_segment = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT,
                                             related_name="derived_segments", editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="created_walkable_segments", editable=False)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="updated_walkable_segments", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=~models.Q(start_node=models.F("end_node")), name="routing_segment_distinct_nodes")]

    @property
    def distance_metres(self):
        return length_metres(self.geometry)

    def clean(self):
        super().clean()
        if self.start_node_id == self.end_node_id:
            raise ValidationError({"end_node": "A segment cannot connect a node to itself."})
        if self.is_active and self.start_node_id and not self.start_node.is_active:
            raise ValidationError({"start_node": "An active segment requires an active start node."})
        if self.is_active and self.end_node_id and not self.end_node.is_active:
            raise ValidationError({"end_node": "An active segment requires an active end node."})
        length_metres(self.geometry)
        points = self.geometry["coordinates"]
        expected_start = (float(self.start_node.longitude), float(self.start_node.latitude))
        expected_end = (float(self.end_node.longitude), float(self.end_node.latitude))
        if distance_metres(points[0], expected_start) > 1 or distance_metres(points[-1], expected_end) > 1:
            raise ValidationError({"geometry": "LineString endpoints must match the selected nodes."})

    def calculate_geometry_fingerprint(self):
        payload = {
            "start": str(self.start_node_id), "end": str(self.end_node_id),
            "geometry": self.geometry, "bidirectional": self.is_bidirectional,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def save(self, *args, **kwargs):
        if not self.geometry_fingerprint:
            self.geometry_fingerprint = self.calculate_geometry_fingerprint()
        super().save(*args, **kwargs)


class PathSurvey(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        COMPLETED = "COMPLETED", "Completed"
        REVIEWED = "REVIEWED", "Reviewed"
        ABANDONED = "ABANDONED", "Abandoned"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="path_surveys")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="reviewed_path_surveys")
    review_note = models.TextField(blank=True, max_length=2000)
    active_capture_seconds = models.PositiveIntegerField(default=0)
    active_capture_tracking_started = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [("conduct_path_survey", "Can conduct path surveys"),
                       ("review_path_survey", "Can review path surveys")]
        ordering = ("-created_at",)

    @property
    def interrupted(self):
        return self.status == self.Status.ACTIVE

    @property
    def session_duration_seconds(self):
        if not self.started_at:
            return 0
        end = self.completed_at or timezone.now()
        return max(0, round((end - self.started_at).total_seconds()))

    @staticmethod
    def format_duration(seconds):
        seconds = max(0, int(seconds or 0))
        return f"{seconds // 60}:{seconds % 60:02d}"

    @property
    def active_capture_display(self):
        return self.format_duration(self.active_capture_seconds)

    @property
    def session_duration_display(self):
        return self.format_duration(self.session_duration_seconds)


class PathSurveySample(models.Model):
    class Classification(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Accepted"
        WEAK = "WEAK", "Weak"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(PathSurvey, on_delete=models.PROTECT, related_name="samples")
    sequence = models.PositiveIntegerField()
    captured_at = models.DateTimeField()
    latitude = models.DecimalField(max_digits=8, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    accuracy_metres = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0)])
    classification = models.CharField(max_length=12, choices=Classification.choices)
    rejection_reason = models.CharField(max_length=120, blank=True)
    speed_metres_per_second = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    heading_degrees = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("survey", "sequence"), name="routing_survey_sample_sequence")]
        ordering = ("sequence",)

    def save(self, *args, **kwargs):
        if self.survey.status in (PathSurvey.Status.COMPLETED, PathSurvey.Status.REVIEWED,
                                  PathSurvey.Status.ABANDONED):
            raise ValidationError("Completed, reviewed and abandoned survey evidence is immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.survey.status in (PathSurvey.Status.COMPLETED, PathSurvey.Status.REVIEWED):
            raise ValidationError("Completed survey evidence cannot be deleted.")
        return super().delete(*args, **kwargs)


class SurveySegmentMatch(models.Model):
    class Classification(models.TextChoices):
        STRONG = "STRONG", "Strong match"
        PARTIAL = "PARTIAL", "Partial match"
        AMBIGUOUS = "AMBIGUOUS", "Ambiguous match"
        DISCREPANCY = "DISCREPANCY", "Possible discrepancy"
    class Disposition(models.TextChoices):
        PENDING = "PENDING", "Pending review"
        ACCEPTED = "ACCEPTED", "Accepted"
        USEFUL_PARTIAL = "USEFUL_PARTIAL", "Useful partial evidence"
        REJECTED = "REJECTED", "Rejected"
        DISCREPANCY_CONFIRMED = "DISCREPANCY_CONFIRMED", "Discrepancy confirmed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(PathSurvey, on_delete=models.PROTECT, related_name="segment_matches")
    segment = models.ForeignKey(WalkableSegment, on_delete=models.PROTECT, related_name="survey_matches")
    segment_revision = models.PositiveIntegerField()
    segment_fingerprint = models.CharField(max_length=64)
    classification = models.CharField(max_length=16, choices=Classification.choices)
    coverage_percent = models.DecimalField(max_digits=5, decimal_places=2)
    mean_distance_metres = models.DecimalField(max_digits=7, decimal_places=2)
    disposition = models.CharField(max_length=24, choices=Disposition.choices, default=Disposition.PENDING)
    reviewer_note = models.TextField(blank=True, max_length=2000)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("survey", "segment", "segment_revision"),
                                                  name="routing_unique_survey_segment_revision")]


class SegmentVerificationRecord(models.Model):
    class Action(models.TextChoices):
        GRANTED = "GRANTED", "Granted"
        REVOKED = "REVOKED", "Revoked"
        INVALIDATED = "INVALIDATED", "Invalidated by geometry change"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    segment = models.ForeignKey(WalkableSegment, on_delete=models.PROTECT, related_name="verification_records")
    survey_match = models.ForeignKey(SurveySegmentMatch, null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="verification_records")
    action = models.CharField(max_length=16, choices=Action.choices)
    geometry_revision = models.PositiveIntegerField()
    geometry_fingerprint = models.CharField(max_length=64)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="segment_verification_actions")
    reason = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("grant_field_verified", "Can grant field verification"),
                       ("revoke_field_verified", "Can revoke field verification")]
        ordering = ("-created_at",)


class LocationNetworkAnchor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.OneToOneField(Location, on_delete=models.CASCADE, related_name="network_anchor")
    node = models.ForeignKey(WalkableNode, on_delete=models.PROTECT, related_name="location_anchors")
    verification_state = models.CharField(max_length=20, choices=VerificationState.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.location} → {self.node}"

    def clean(self):
        super().clean()
        if self.is_active and not self.node.is_active:
            raise ValidationError({"node": "An active anchor requires an active walkable node."})


class EntranceNetworkAnchor(models.Model):
    MAX_CONNECTOR_LENGTH_METRES = 150

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entrance = models.OneToOneField(Entrance, on_delete=models.CASCADE, related_name="network_anchor")
    node = models.ForeignKey(WalkableNode, on_delete=models.PROTECT, related_name="entrance_anchors")
    connector_geometry = models.JSONField(null=True, blank=True)
    verification_state = models.CharField(max_length=20, choices=VerificationState.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.entrance_id and not self.entrance.is_active and self.is_active:
            raise ValidationError({"entrance": "An active anchor requires an active entrance."})
        if self.is_active and not self.node.is_active:
            raise ValidationError({"node": "An active anchor requires an active walkable node."})
        if self.connector_geometry is not None:
            points = coordinates(self.connector_geometry)
            expected_start = (float(self.node.longitude), float(self.node.latitude))
            expected_end = (float(self.entrance.longitude), float(self.entrance.latitude))
            if points[0] != expected_start:
                raise ValidationError({"connector_geometry": "The connector must begin exactly at its routing node."})
            if points[-1] != expected_end:
                raise ValidationError({"connector_geometry": "The connector must end exactly at the physical entrance point."})
            connector_length = length_metres(self.connector_geometry)
            if connector_length > self.MAX_CONNECTOR_LENGTH_METRES:
                raise ValidationError({
                    "connector_geometry":
                        f"The entrance connector must remain local ({self.MAX_CONNECTOR_LENGTH_METRES} m maximum)."
                })

    @property
    def connector_distance_metres(self):
        return length_metres(self.connector_geometry) if self.connector_geometry else 0.0

    def __str__(self):
        return f"{self.entrance} → {self.node}"
