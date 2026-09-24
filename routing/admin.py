from django.contrib import admin

from .models import EntranceNetworkAnchor, LocationNetworkAnchor, WalkableNode, WalkableSegment


@admin.register(EntranceNetworkAnchor)
class EntranceNetworkAnchorAdmin(admin.ModelAdmin):
    list_display = ("entrance", "node", "is_active", "verification_state", "updated_at")
    list_filter = ("is_active", "verification_state")
    search_fields = ("entrance__name", "entrance__location__name", "node__label")


admin.site.register(LocationNetworkAnchor)
admin.site.register(WalkableNode)
admin.site.register(WalkableSegment)
