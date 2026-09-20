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
    }
    permissions = Permission.objects.filter(
        content_type__app_label="locations",
        codename__in=permission_names,
    )
    group.permissions.set(permissions)


class LocationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "locations"

    def ready(self):
        from django.db.models.signals import post_migrate

        post_migrate.connect(ensure_editor_group, sender=self, dispatch_uid="locations.ensure_editor_group")
