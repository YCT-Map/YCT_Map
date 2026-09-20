from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import LocationAliasFormSet, LocationForm
from .models import Location


class EditorLoginView(LoginView):
    template_name = "editor/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or str(reverse_lazy("editor:dashboard"))


def active_editor(permission):
    def decorator(view):
        @login_required(login_url="editor:login")
        @permission_required(permission, raise_exception=True)
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_active:
                return HttpResponseForbidden("This editor account is inactive.")
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


@require_GET
@active_editor("locations.view_location")
def dashboard(request):
    return render(
        request,
        "editor/dashboard.html",
        {
            "place_count": Location.objects.count(),
            "draft_count": Location.objects.filter(publication_status=Location.PublicationStatus.DRAFT).count(),
        },
    )


@require_GET
@active_editor("locations.view_location")
def place_list(request):
    places = Location.objects.prefetch_related("categories").order_by("name")
    return render(request, "editor/place_list.html", {"places": places})


def _can_edit(request):
    return request.user.has_perm("locations.change_location")


@require_http_methods(["GET", "POST"])
@active_editor("locations.add_location")
def place_create(request):
    location = Location(
        publication_status=Location.PublicationStatus.DRAFT,
        verification_state=Location.VerificationState.UNVERIFIED,
    )
    return _place_form(request, location, creating=True)


@require_http_methods(["GET", "POST"])
@active_editor("locations.view_location")
def place_detail(request, place_id):
    location = get_object_or_404(Location, pk=place_id)
    if request.method == "POST" and not _can_edit(request):
        return HttpResponseForbidden("You do not have permission to edit places.")
    return _place_form(request, location, creating=False)


def _place_form(request, location, creating):
    can_edit = creating or _can_edit(request)
    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)
        aliases = LocationAliasFormSet(request.POST, instance=location, prefix="aliases")
        if form.is_valid() and aliases.is_valid():
            with transaction.atomic():
                saved = form.save(commit=False)
                if creating:
                    saved.created_by = request.user
                saved.updated_by = request.user
                saved.is_active = saved.publication_status == Location.PublicationStatus.PUBLISHED
                saved.full_clean(exclude=("categories",))
                saved.save()
                form.save_m2m()
                form._sync_legacy_category(saved)
                aliases.instance = saved
                alias_objects = aliases.save(commit=False)
                for deleted in aliases.deleted_objects:
                    deleted.delete()
                for alias in alias_objects:
                    alias.location = saved
                    alias.full_clean()
                    alias.save()
            messages.success(request, "Place saved.")
            return redirect("editor:place-detail", place_id=saved.pk)
    else:
        form = LocationForm(instance=location)
        aliases = LocationAliasFormSet(instance=location, prefix="aliases")
        if not can_edit:
            for field in form.fields.values():
                field.disabled = True
            for alias_form in aliases.forms:
                for field in alias_form.fields.values():
                    field.disabled = True
    return render(
        request,
        "editor/place_form.html",
        {"form": form, "aliases": aliases, "place": location, "creating": creating, "can_edit": can_edit},
    )


@require_POST
@active_editor("locations.change_location")
def place_archive(request, place_id):
    location = get_object_or_404(Location, pk=place_id)
    location.publication_status = Location.PublicationStatus.ARCHIVED
    location.is_active = False
    location.updated_by = request.user
    location.full_clean(exclude=("categories",))
    location.save(update_fields=("publication_status", "is_active", "updated_by", "updated_at"))
    messages.success(request, "Place archived.")
    return redirect("editor:place-detail", place_id=location.pk)


@require_POST
@active_editor("locations.change_location")
def place_reactivate(request, place_id):
    location = get_object_or_404(Location, pk=place_id)
    requested_status = request.POST.get("publication_status", Location.PublicationStatus.DRAFT)
    if requested_status not in {Location.PublicationStatus.DRAFT, Location.PublicationStatus.PUBLISHED}:
        return HttpResponseForbidden("Invalid reactivation state.")
    location.publication_status = requested_status
    location.is_active = requested_status == Location.PublicationStatus.PUBLISHED
    location.updated_by = request.user
    location.full_clean(exclude=("categories",))
    location.save(update_fields=("publication_status", "is_active", "updated_by", "updated_at"))
    messages.success(request, "Place reactivated.")
    return redirect("editor:place-detail", place_id=location.pk)
