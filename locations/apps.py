from django.apps import AppConfig


def ensure_editor_group(sender, **kwargs):
    """Provision the least-privilege Editor group after migrations."""
    from django.contrib.auth.models import Group, Permission

    group, _ = Group.objects.get_or_create(name="Editor")
    permission_names = {
        "view_location",
        "add_location",
        "change_location",
        "view_locationalias",
        "add_locationalias",
        "change_locationalias",
        "delete_locationalias",
        "view_category",
        "view_entrance", "add_entrance", "change_entrance",
        "view_floor", "add_floor", "change_floor",
        "view_internalplace", "add_internalplace", "change_internalplace",
        "view_internalplacealias", "add_internalplacealias", "change_internalplacealias", "delete_internalplacealias",
        "resolve_contribution",
        "view_walkablenode", "add_walkablenode", "change_walkablenode",
        "view_walkablesegment", "add_walkablesegment", "change_walkablesegment",
    }
    permissions = Permission.objects.filter(
        content_type__app_label__in=("locations", "contributions", "routing"),
        codename__in=permission_names,
    )
    group.permissions.set(permissions)


class LocationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "locations"

    def ready(self):
        from django.db.models.signals import post_migrate

        # Run after every migrated app so permissions created by contributions/routing
        # are included regardless of application post_migrate ordering.
        post_migrate.connect(ensure_editor_group, dispatch_uid="locations.ensure_editor_group")
