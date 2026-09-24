import uuid

from django.conf import settings

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from locations.models import Entrance, Location

from .geometry import distance_metres, length_metres


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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entrance = models.OneToOneField(Entrance, on_delete=models.CASCADE, related_name="network_anchor")
    node = models.ForeignKey(WalkableNode, on_delete=models.PROTECT, related_name="entrance_anchors")
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

    def __str__(self):
        return f"{self.entrance} → {self.node}"
