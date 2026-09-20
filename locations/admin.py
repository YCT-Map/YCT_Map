from django.contrib import admin

from .models import Category, Location, LocationAlias


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "display_order", "legacy_filter")
    list_editable = ("is_active", "display_order")
    search_fields = ("name", "slug")


class LocationAliasInline(admin.TabularInline):
    model = LocationAlias
    extra = 0


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "place_type", "publication_status", "verification_state", "updated_at")
    list_filter = ("place_type", "publication_status", "verification_state")
    search_fields = ("name", "aliases__name")
    readonly_fields = ("id", "created_by", "updated_by", "created_at", "updated_at")
    filter_horizontal = ("categories",)
    inlines = (LocationAliasInline,)
