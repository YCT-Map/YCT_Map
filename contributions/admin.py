from django.contrib import admin
from django.utils import timezone

from .models import Contribution


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ("contribution_type", "status", "target_location", "proposed_name", "created_at", "reviewed_by")
    list_filter = ("status", "contribution_type", "created_at")
    search_fields = ("proposed_name", "description", "target_location__name")
    readonly_fields = ("id", "request_id", "created_at", "reviewed_at", "reviewed_by")
    raw_id_fields = ("target_location", "merged_into", "resolved_location")

    def save_model(self, request, obj, form, change):
        if obj.status != Contribution.Status.PENDING:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        else:
            obj.reviewed_by = None
            obj.reviewed_at = None
        obj.full_clean()
        super().save_model(request, obj, form, change)
