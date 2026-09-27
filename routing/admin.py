from django.contrib import admin

from .models import (EntranceNetworkAnchor, LocationNetworkAnchor, PathSurvey, PathSurveySample,
                     SegmentVerificationRecord, SurveySegmentMatch, WalkableNode, WalkableSegment)


class ReadOnlyRoutingAuditAdmin(admin.ModelAdmin):
    """Expose routing evidence for inspection without creating a bypass write path."""

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EntranceNetworkAnchor)
class EntranceNetworkAnchorAdmin(admin.ModelAdmin):
    list_display = ("entrance", "node", "is_active", "verification_state", "updated_at")
    list_filter = ("is_active", "verification_state")
    search_fields = ("entrance__name", "entrance__location__name", "node__label")
    readonly_fields = ("connector_geometry",)


admin.site.register(LocationNetworkAnchor)


@admin.register(WalkableNode)
class WalkableNodeAdmin(ReadOnlyRoutingAuditAdmin):
    list_display = ("label", "longitude", "latitude", "verification_state", "source_type", "is_active")
    list_filter = ("verification_state", "source_type", "is_active")
    search_fields = ("label", "source_reference")


@admin.register(WalkableSegment)
class WalkableSegmentAdmin(ReadOnlyRoutingAuditAdmin):
    list_display = ("label", "start_node", "end_node", "geometry_revision", "verification_state", "is_active")
    list_filter = ("verification_state", "source_type", "is_active", "is_bidirectional")
    search_fields = ("label", "source_reference")


@admin.register(PathSurvey)
class PathSurveyAdmin(ReadOnlyRoutingAuditAdmin):
    list_display = ("id", "owner", "status", "started_at", "completed_at", "reviewed_at")
    list_filter = ("status",)


@admin.register(PathSurveySample)
class PathSurveySampleAdmin(ReadOnlyRoutingAuditAdmin):
    list_display = ("survey", "sequence", "captured_at", "accuracy_metres", "classification")
    list_filter = ("classification",)


@admin.register(SurveySegmentMatch)
class SurveySegmentMatchAdmin(ReadOnlyRoutingAuditAdmin):
    list_display = ("survey", "segment", "segment_revision", "classification", "coverage_percent", "disposition")
    list_filter = ("classification", "disposition")


@admin.register(SegmentVerificationRecord)
class SegmentVerificationRecordAdmin(ReadOnlyRoutingAuditAdmin):
    list_display = ("segment", "action", "geometry_revision", "actor", "created_at")
    list_filter = ("action",)
