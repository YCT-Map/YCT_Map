import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from locations.models import Location

from .geometry import distance_metres, length_metres


class VerificationState(models.TextChoices):
    DEMO = "DEMO", "Demonstration data"
    UNVERIFIED = "UNVERIFIED", "Unverified"
    FIELD_VERIFIED = "FIELD_VERIFIED", "Field verified"


class WalkableNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=120, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    latitude = models.DecimalField(max_digits=8, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    verification_state = models.CharField(max_length=20, choices=VerificationState.choices)
    is_active = models.BooleanField(default=True)
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
    is_active = models.BooleanField(default=True)
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
