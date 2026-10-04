from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
import json
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import (EntranceForm, FloorForm, InternalPlaceAliasFormSet,
                    InternalPlaceForm, LocationAliasFormSet, LocationForm)
from .models import Entrance, Floor, InternalPlace, Location
from routing.destinations import resolve_destination
from contributions.editor_forms import ContributionResolutionForm
from contributions.models import Contribution
from routing.editor_forms import SplitSegmentForm, WalkableNodeForm, WalkableSegmentForm
from routing.editor_services import (MAX_ENTRANCE_NODE_METRES, NEARBY_ENTRANCE_NODE_METRES,
                                     connect_entrance_to_node, disconnect_entrance_from_network,
                                     entrance_candidate_map_data, entrance_node_candidates,
                                     save_segment, segment_impact, split_segment)
from routing.models import (EntranceNetworkAnchor, PathSurvey, SourceType, SurveySegmentMatch,
                            VerificationState, WalkableNode, WalkableSegment)
from routing.geometry import distance_metres
from routing.survey_services import (MATCH_DISTANCE_METRES, analyse_survey_dry_run,
                                     apply_finalized_evidence, decide_verification,
                                     evaluate_finalized_evidence, finalized_evidence_summary,
                                     record_match_review, store_samples, transition_survey)
from routing.matching import project_onto_segment
from routing.candidate_services import create_candidate_path, preview_candidate_graph_change
from django.utils.dateparse import parse_datetime
from django.db.models import Count, Q


NEARBY_CANDIDATE_LANDMARK_METRES = 120
CANDIDATE_LANDMARK_CONTEXT_METRES = 400


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


def active_editor_any(*permissions):
    """Require an active account with at least one explicitly listed permission."""
    def decorator(view):
        @login_required(login_url="editor:login")
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_active:
                return HttpResponseForbidden("This editor account is inactive.")
            if not any(request.user.has_perm(permission) for permission in permissions):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def _redirect_to_place_or(request, target_place_id, fallback_name, **fallback_kwargs):
    if request.user.has_perm("locations.view_location") or request.user.has_perm("locations.change_location"):
        return redirect("editor:place-detail", place_id=target_place_id)
    return redirect(f"editor:{fallback_name}", **fallback_kwargs)


def _redirect_to_paths_or(request, fallback_name, **fallback_kwargs):
    if request.user.has_perm("routing.view_walkablesegment"):
        return redirect("editor:path-list")
    return redirect(f"editor:{fallback_name}", **fallback_kwargs)


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
@active_editor_any("locations.view_location", "locations.change_location")
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
                if any(name in form.changed_data for name in ("representative_latitude", "representative_longitude")):
                    saved.verification_state = Location.VerificationState.UNVERIFIED
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
                if form.cleaned_data.get("capture_primary_entrance"):
                    primary = saved.entrances.filter(is_primary=True, is_active=True).first()
                    if primary:
                        primary.latitude = saved.representative_latitude
                        primary.longitude = saved.representative_longitude
                        primary.verification_state = Location.VerificationState.UNVERIFIED
                        primary.updated_by = request.user
                        primary.full_clean()
                        primary.save()
                    else:
                        primary = Entrance(
                            location=saved, name=f"{saved.name} — Primary entrance",
                            entrance_type=Entrance.Type.MAIN, latitude=saved.representative_latitude,
                            longitude=saved.representative_longitude, is_primary=True, is_active=True,
                            verification_state=Location.VerificationState.UNVERIFIED,
                            created_by=request.user, updated_by=request.user,
                        )
                        primary.full_clean()
                        primary.save()
            messages.success(request, "Place saved.")
            return _redirect_to_place_or(request, saved.pk, "place-create")
    else:
        form = LocationForm(instance=location)
        aliases = LocationAliasFormSet(instance=location, prefix="aliases")
        if not can_edit:
            for field in form.fields.values():
                field.disabled = True
            for alias_form in aliases.forms:
                for field in alias_form.fields.values():
                    field.disabled = True
    routing = None
    persisted_published = (
        bool(location.pk) and not location._state.adding and
        Location.objects.filter(pk=location.pk, publication_status=Location.PublicationStatus.PUBLISHED).exists()
    )
    if persisted_published:
        try:
            routing = resolve_destination(f"location:{location.pk}")
        except ValidationError:
            # Editor detail must represent incomplete routing as state, never leak
            # a public destination resolver exception into a form response.
            routing = None
    return render(
        request,
        "editor/place_form.html",
        {"form": form, "aliases": aliases, "place": location, "creating": creating, "can_edit": can_edit,
         "routing": routing, "entrances": location.entrances.all() if location.pk else (),
         "floors": location.floors.all() if location.pk else (),
         "internal_places": location.internal_places.select_related("floor") if location.pk else (),
         "can_grant_place_verification": can_edit and request.user.has_perm("routing.grant_field_verified"),
         "can_revoke_place_verification": can_edit and request.user.has_perm("routing.revoke_field_verified")},
    )


def _save_audited(form, request, creating):
    item = form.save(commit=False)
    if creating:
        item.created_by = request.user
    item.updated_by = request.user
    item.full_clean()
    item.save()
    return item


def _entrance_editor_context(request, form, location, entrance, *, creating):
    anchor = None
    anchor_distance = None
    if not creating:
        anchor = EntranceNetworkAnchor.objects.filter(entrance=entrance).select_related("node").first()
        if anchor and anchor.is_active:
            anchor_distance = anchor.connector_distance_metres if anchor.connector_geometry else distance_metres(
                (float(entrance.longitude), float(entrance.latitude)),
                (float(anchor.node.longitude), float(anchor.node.latitude)),
            )
    return {
        "form": form,
        "place": location,
        "entrance": entrance,
        "creating": creating,
        "network_anchor": anchor,
        "network_anchor_distance": anchor_distance,
        "can_grant_entrance_verification": request.user.has_perm("routing.grant_field_verified"),
        "can_revoke_entrance_verification": request.user.has_perm("routing.revoke_field_verified"),
    }


@require_http_methods(["GET", "POST"])
@active_editor("locations.add_entrance")
def entrance_create(request, place_id):
    location = get_object_or_404(Location, pk=place_id)
    entrance = Entrance(location=location)
    form = EntranceForm(request.POST or None, instance=entrance)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            if form.cleaned_data["is_primary"]:
                location.entrances.filter(is_primary=True).update(is_primary=False)
            entrance = _save_audited(form, request, True)
        messages.success(request, "Entrance saved.")
        return _redirect_to_place_or(request, place_id, "entrance-create", place_id=place_id)
    return render(request, "editor/entrance_form.html", _entrance_editor_context(
        request, form, location, entrance, creating=True,
    ))


@require_http_methods(["GET", "POST"])
@active_editor("locations.change_entrance")
def entrance_edit(request, place_id, entrance_id):
    location = get_object_or_404(Location, pk=place_id)
    entrance = get_object_or_404(Entrance, pk=entrance_id, location=location)
    form = EntranceForm(request.POST or None, instance=entrance)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            if form.cleaned_data["is_primary"]:
                location.entrances.exclude(pk=entrance.pk).filter(is_primary=True).update(is_primary=False)
            saved = form.save(commit=False)
            if any(name in form.changed_data for name in ("latitude", "longitude")):
                saved.verification_state = Location.VerificationState.UNVERIFIED
            saved.updated_by = request.user
            saved.full_clean(); saved.save()
        messages.success(request, "Entrance saved.")
        return _redirect_to_place_or(
            request, place_id, "entrance-edit", place_id=place_id, entrance_id=entrance.pk,
        )
    return render(request, "editor/entrance_form.html", _entrance_editor_context(
        request, form, location, entrance, creating=False,
    ))


def _apply_field_verification(request, item, *, label, redirect_name, redirect_args):
    action = request.POST.get("action")
    permission = "routing.grant_field_verified" if action == "grant" else "routing.revoke_field_verified"
    if action not in {"grant", "revoke"}:
        return HttpResponseForbidden("Choose a valid verification action.")
    if not request.user.has_perm(permission):
        raise PermissionDenied
    reason = request.POST.get("reason", "").strip()
    if not reason:
        messages.error(request, "A verification reason is required.")
        return redirect(redirect_name, *redirect_args)
    item.verification_state = (Location.VerificationState.FIELD_VERIFIED
                               if action == "grant" else Location.VerificationState.UNVERIFIED)
    item.updated_by = request.user
    item.save(update_fields=("verification_state", "updated_by", "updated_at"))
    messages.success(request, f"{label} field verification {'granted' if action == 'grant' else 'revoked'}.")
    return redirect(redirect_name, *redirect_args)


@require_POST
@active_editor("locations.change_location")
def place_verification(request, place_id):
    location = get_object_or_404(Location, pk=place_id)
    return _apply_field_verification(request, location, label="Place",
                                     redirect_name="editor:place-detail", redirect_args=(location.pk,))


@require_POST
@active_editor("locations.change_entrance")
def entrance_verification(request, place_id, entrance_id):
    location = get_object_or_404(Location, pk=place_id)
    entrance = get_object_or_404(Entrance, pk=entrance_id, location=location)
    return _apply_field_verification(request, entrance, label="Entrance",
                                     redirect_name="editor:entrance-edit",
                                     redirect_args=(location.pk, entrance.pk))


@require_GET
@active_editor("locations.change_entrance")
def entrance_connection_candidates(request, place_id, entrance_id):
    if not request.user.has_perm("routing.view_walkablenode") or not request.user.has_perm(
        "routing.view_entrancenetworkanchor"
    ):
        raise PermissionDenied
    location = get_object_or_404(Location, pk=place_id)
    entrance = get_object_or_404(Entrance, pk=entrance_id, location=location)
    candidates = entrance_node_candidates(entrance)
    map_data = entrance_candidate_map_data(entrance, candidates)
    current_anchor = EntranceNetworkAnchor.objects.filter(entrance=entrance, is_active=True).first()
    return JsonResponse({
        "entrance": {
            "id": str(entrance.pk),
            "name": entrance.name,
            "latitude": float(entrance.latitude),
            "longitude": float(entrance.longitude),
        },
        "policy": {
            "nearby_metres": NEARBY_ENTRANCE_NODE_METRES,
            "maximum_metres": MAX_ENTRANCE_NODE_METRES,
            "explanation": "Nodes within 40 m are nearby; nodes from 40–75 m require extra review.",
        },
        "candidates": [feature["properties"] | {
            "longitude": feature["geometry"]["coordinates"][0],
            "latitude": feature["geometry"]["coordinates"][1],
        } for feature in map_data["features"]
          if feature["properties"]["kind"] == "candidate"],
        "map": map_data,
        "current_connection": {
            "node_id": str(current_anchor.node_id),
            "connector_geometry": current_anchor.connector_geometry,
        } if current_anchor else None,
    })


@require_POST
@active_editor("locations.change_entrance")
def entrance_connection_update(request, place_id, entrance_id):
    location = get_object_or_404(Location, pk=place_id)
    entrance = get_object_or_404(Entrance, pk=entrance_id, location=location)
    action = request.POST.get("action")
    if action == "disconnect":
        if not request.user.has_perm("routing.change_entrancenetworkanchor"):
            raise PermissionDenied
        if request.POST.get("confirm_disconnect") != "yes":
            messages.error(request, "Confirm that you intend to disconnect this entrance.")
        else:
            disconnect_entrance_from_network(entrance=entrance)
            messages.success(request, "Entrance disconnected from the walking network.")
        return redirect("editor:entrance-edit", place_id=location.pk, entrance_id=entrance.pk)
    if action != "connect":
        return HttpResponseForbidden("Unknown routing-connection action.")
    existing = EntranceNetworkAnchor.objects.filter(entrance=entrance).exists()
    required_permission = "routing.change_entrancenetworkanchor" if existing else "routing.add_entrancenetworkanchor"
    if not request.user.has_perm(required_permission) or not request.user.has_perm("routing.view_walkablenode"):
        raise PermissionDenied
    try:
        node = WalkableNode.objects.get(pk=request.POST.get("node_id"))
    except (WalkableNode.DoesNotExist, ValidationError, ValueError, TypeError):
        messages.error(request, "Choose a valid routing-node candidate before confirming.")
        return redirect("editor:entrance-edit", place_id=location.pk, entrance_id=entrance.pk)
    try:
        connector_geometry = json.loads(request.POST.get("connector_geometry", ""))
    except (json.JSONDecodeError, TypeError):
        messages.error(request, "Provide a valid approved arrival connector before confirming.")
        return redirect("editor:entrance-edit", place_id=location.pk, entrance_id=entrance.pk)
    try:
        connect_entrance_to_node(entrance=entrance, node=node, connector_geometry=connector_geometry)
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(request, "Entrance connected to the walking network as UNVERIFIED data.")
    return redirect("editor:entrance-edit", place_id=location.pk, entrance_id=entrance.pk)


@require_http_methods(["GET", "POST"])
@active_editor("locations.add_floor")
def floor_create(request, place_id):
    location = get_object_or_404(Location, pk=place_id)
    floor = Floor(location=location)
    form = FloorForm(request.POST or None, instance=floor)
    if request.method == "POST" and form.is_valid():
        _save_audited(form, request, True)
        messages.success(request, "Floor saved.")
        return _redirect_to_place_or(request, place_id, "floor-create", place_id=place_id)
    return render(request, "editor/simple_form.html", {"form": form, "place": location, "heading": "Add floor"})


@require_http_methods(["GET", "POST"])
@active_editor("locations.change_floor")
def floor_edit(request, place_id, floor_id):
    location = get_object_or_404(Location, pk=place_id)
    floor = get_object_or_404(Floor, pk=floor_id, location=location)
    form = FloorForm(request.POST or None, instance=floor)
    if request.method == "POST" and form.is_valid():
        _save_audited(form, request, False)
        messages.success(request, "Floor saved.")
        return _redirect_to_place_or(
            request, place_id, "floor-edit", place_id=place_id, floor_id=floor.pk,
        )
    return render(request, "editor/simple_form.html", {"form": form, "place": location, "heading": "Edit floor"})


@require_http_methods(["GET", "POST"])
@active_editor("locations.add_internalplace")
def internal_create(request, place_id):
    location = get_object_or_404(Location, pk=place_id)
    item = InternalPlace(location=location)
    form = InternalPlaceForm(request.POST or None, instance=item, location=location)
    aliases = InternalPlaceAliasFormSet(request.POST or None, instance=item, prefix="aliases")
    if request.method == "POST" and form.is_valid() and aliases.is_valid():
        with transaction.atomic():
            item = _save_audited(form, request, True)
            aliases.instance = item
            aliases.save()
        messages.success(request, "Internal place saved. Add another or return to the building.")
        if "add_another" in request.POST:
            return redirect(f"{request.path}?floor={item.floor_id or ''}")
        return _redirect_to_place_or(request, place_id, "internal-create", place_id=place_id)
    if request.method == "GET" and request.GET.get("floor"):
        form.fields["floor"].initial = request.GET["floor"]
    return render(request, "editor/internal_form.html", {"form": form, "aliases": aliases, "place": location})


@require_http_methods(["GET", "POST"])
@active_editor("locations.change_internalplace")
def internal_edit(request, place_id, internal_id):
    location = get_object_or_404(Location, pk=place_id)
    item = get_object_or_404(InternalPlace, pk=internal_id, location=location)
    form = InternalPlaceForm(request.POST or None, instance=item, location=location)
    aliases = InternalPlaceAliasFormSet(request.POST or None, instance=item, prefix="aliases")
    if request.method == "POST" and form.is_valid() and aliases.is_valid():
        with transaction.atomic():
            _save_audited(form, request, False)
            aliases.save()
        messages.success(request, "Internal place saved.")
        return _redirect_to_place_or(
            request, place_id, "internal-edit", place_id=place_id, internal_id=item.pk,
        )
    return render(request, "editor/internal_form.html", {"form": form, "aliases": aliases, "place": location, "item": item})


@require_POST
@active_editor("locations.change_location")
def place_archive(request, place_id):
    location = get_object_or_404(Location, pk=place_id)
    location.publication_status = Location.PublicationStatus.ARCHIVED
    location.is_active = False
    location.updated_by = request.user
    try:
        location.full_clean(exclude=("categories",))
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
        return redirect("editor:place-detail", place_id=location.pk)
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
    try:
        location.full_clean(exclude=("categories",))
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
        return redirect("editor:place-detail", place_id=location.pk)
    location.save(update_fields=("publication_status", "is_active", "updated_by", "updated_at"))
    messages.success(request, "Place reactivated.")
    return redirect("editor:place-detail", place_id=location.pk)


@require_GET
@active_editor("contributions.resolve_contribution")
def contribution_list(request):
    items = Contribution.objects.filter(status=Contribution.Status.APPROVED).prefetch_related("resolutions")
    return render(request, "editor/contribution_list.html", {"contributions": items})


@require_http_methods(["GET", "POST"])
@active_editor("contributions.resolve_contribution")
def contribution_detail(request, contribution_id):
    contribution = get_object_or_404(Contribution, pk=contribution_id, status=Contribution.Status.APPROVED)
    form = ContributionResolutionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        resolution = form.save(commit=False)
        resolution.contribution = contribution
        resolution.resolved_by = request.user
        resolution.full_clean()
        resolution.save()
        messages.success(request, "Resolution action recorded. Approval and campus publication remain separate.")
        return redirect("editor:contribution-detail", contribution_id=contribution.pk)
    return render(request, "editor/contribution_detail.html", {"contribution": contribution, "form": form})


@require_GET
@active_editor("routing.view_walkablesegment")
def path_list(request):
    nodes = WalkableNode.objects.all()
    segments = WalkableSegment.objects.select_related("start_node", "end_node")
    overview = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": segment.geometry,
             "properties": {"kind": "segment", "id": str(segment.id), "source": segment.source_type,
                            "label": segment.label, "active": segment.is_active}}
            for segment in segments if segment.is_active
        ] + [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(node.longitude), float(node.latitude)]},
             "properties": {"kind": "node", "id": str(node.id), "source": node.source_type,
                            "label": node.label, "active": node.is_active}}
            for node in nodes if node.is_active
        ],
    }
    focus = None
    try:
        latitude = float(request.GET.get("latitude", ""))
        longitude = float(request.GET.get("longitude", ""))
        if -90 <= latitude <= 90 and -180 <= longitude <= 180:
            focus = {"latitude": latitude, "longitude": longitude}
    except (TypeError, ValueError):
        pass
    return render(request, "editor/path_list.html", {
        "nodes": nodes, "segments": segments, "overview": overview, "focus": focus,
    })


@require_http_methods(["GET", "POST"])
@active_editor("routing.add_walkablenode")
def node_create(request):
    item = WalkableNode(source_type=SourceType.MANUAL, verification_state=VerificationState.UNVERIFIED)
    form = WalkableNodeForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False); item.created_by = item.updated_by = request.user; item.full_clean(); item.save()
        messages.success(request, "UNVERIFIED routing node created.")
        return _redirect_to_paths_or(request, "node-create")
    return render(request, "editor/node_form.html", {
        "form": form, "node": item, "locked": False, "creating": True,
    })


@require_http_methods(["GET", "POST"])
@active_editor("routing.change_walkablenode")
def node_edit(request, node_id):
    item = get_object_or_404(WalkableNode, pk=node_id)
    locked = item.outgoing_segments.exists() or item.incoming_segments.exists()
    form = WalkableNodeForm(request.POST or None, instance=item, locked=locked)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False); item.updated_by = request.user; item.full_clean(); item.save()
        messages.success(request, "Routing node saved.")
        return _redirect_to_paths_or(request, "node-edit", node_id=item.pk)
    return render(request, "editor/node_form.html", {
        "form": form, "node": item, "locked": locked, "creating": False,
    })


@require_http_methods(["GET", "POST"])
@active_editor("routing.add_walkablesegment")
def segment_create(request):
    item = WalkableSegment(source_type=SourceType.MANUAL, verification_state=VerificationState.UNVERIFIED)
    form = WalkableSegmentForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False); save_segment(segment=item, cleaned_data=form.cleaned_data, actor=request.user)
        messages.success(request, "UNVERIFIED path segment created.")
        return _redirect_to_paths_or(request, "segment-create")
    nodes = list(WalkableNode.objects.filter(is_active=True).values("id", "longitude", "latitude", "label"))
    return render(request, "editor/segment_form.html", {
        "form": form, "segment": item, "impact": (), "nodes_json": nodes, "creating": True,
    })


@require_http_methods(["GET", "POST"])
@active_editor("routing.change_walkablesegment")
def segment_edit(request, segment_id):
    item = get_object_or_404(WalkableSegment, pk=segment_id)
    impact = segment_impact(item)
    form = WalkableSegmentForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False); save_segment(segment=item, cleaned_data=form.cleaned_data, actor=request.user)
        messages.success(request, "Path segment saved.")
        return _redirect_to_paths_or(request, "segment-edit", segment_id=item.pk)
    nodes = list(WalkableNode.objects.filter(is_active=True).values("id", "longitude", "latitude", "label"))
    return render(request, "editor/segment_form.html", {
        "form": form, "segment": item, "impact": impact, "nodes_json": nodes, "creating": False,
    })


@require_http_methods(["GET", "POST"])
@active_editor("routing.change_walkablesegment")
def segment_split(request, segment_id):
    item = get_object_or_404(WalkableSegment, pk=segment_id, is_active=True)
    form = SplitSegmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            split_segment(item, (float(form.cleaned_data["longitude"]), float(form.cleaned_data["latitude"])), request.user)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Segment split transaction completed; the original remains inactive for history.")
            return _redirect_to_paths_or(request, "segment-edit", segment_id=item.pk)
    return render(request, "editor/segment_split.html", {"form": form, "segment": item})


@require_GET
@active_editor_any("routing.conduct_path_survey", "routing.review_path_survey")
def survey_list(request):
    return render(request, "editor/survey_list.html", _survey_list_context(request))


def _survey_list_context(request, *, historical_preview=None):
    surveys = PathSurvey.objects.select_related("owner", "reviewed_by")
    if not request.user.has_perm("routing.review_path_survey"):
        surveys = surveys.filter(owner=request.user)
    return {
        "surveys": surveys,
        "historical_preview": historical_preview,
        "can_review_historical": request.user.has_perm("routing.review_path_survey"),
        "can_apply_historical": request.user.has_perm("routing.review_path_survey")
        and request.user.has_perm("routing.grant_field_verified"),
    }


@require_POST
@active_editor("routing.review_path_survey")
def survey_re_evaluate(request):
    action = request.POST.get("action")
    if action == "preview":
        preview = finalized_evidence_summary(evaluate_finalized_evidence())
        return render(request, "editor/survey_list.html", _survey_list_context(
            request, historical_preview=preview,
        ))
    if action != "apply" or request.POST.get("confirm") != "yes":
        messages.error(request, "Preview the results and explicitly confirm before applying verification.")
        return redirect("editor:survey-list")
    if not request.user.has_perm("routing.grant_field_verified"):
        raise PermissionDenied
    applied = apply_finalized_evidence(actor=request.user)
    messages.success(
        request,
        f"Historical evidence re-evaluated. {len(applied['promoted_segment_ids'])} existing "
        "path segment(s) became FIELD_VERIFIED. No path geometry or survey status changed.",
    )
    return redirect("editor:survey-list")


@require_POST
@active_editor("routing.conduct_path_survey")
def survey_create(request):
    survey = PathSurvey.objects.create(owner=request.user)
    return redirect("editor:survey-detail", survey_id=survey.pk)


@require_http_methods(["GET", "POST"])
@active_editor_any("routing.conduct_path_survey", "routing.review_path_survey")
def survey_detail(request, survey_id):
    survey = get_object_or_404(PathSurvey.objects.select_related("owner", "reviewed_by"), pk=survey_id)
    can_review = request.user.has_perm("routing.review_path_survey")
    if survey.owner_id != request.user.pk and not can_review:
        return HttpResponseForbidden("You cannot access another editor's private survey evidence.")
    if request.method == "POST":
        action = request.POST.get("action")
        if survey.owner_id == request.user.pk and survey.status == PathSurvey.Status.ACTIVE:
            try:
                reported_seconds = max(0, int(request.POST.get("active_capture_seconds", 0)))
            except (TypeError, ValueError):
                reported_seconds = survey.active_capture_seconds
            if reported_seconds > survey.active_capture_seconds:
                survey.active_capture_seconds = reported_seconds
                survey.save(update_fields=("active_capture_seconds", "updated_at"))
        target = {"start": PathSurvey.Status.ACTIVE, "pause": PathSurvey.Status.PAUSED,
                  "resume": PathSurvey.Status.ACTIVE, "finish": PathSurvey.Status.COMPLETED,
                  "abandon": PathSurvey.Status.ABANDONED}.get(action)
        if target:
            try: transition_survey(survey, target, request.user)
            except (ValidationError, PermissionDenied) as error: messages.error(request, str(error))
            return redirect("editor:survey-detail", survey_id=survey.pk)
        if action == "mark-reviewed" and can_review and survey.status == PathSurvey.Status.COMPLETED:
            survey.status = PathSurvey.Status.REVIEWED; survey.reviewed_by = request.user
            survey.reviewed_at = __import__("django.utils.timezone", fromlist=["now"]).now()
            survey.review_note = request.POST.get("review_note", "")[:2000]; survey.save()
            messages.success(request, "Survey review status recorded. No graph geometry was changed.")
            return redirect("editor:survey-detail", survey_id=survey.pk)
    counts = survey.samples.aggregate(raw=Count("id"),
        accepted=Count("id", filter=Q(classification="ACCEPTED")),
        weak=Count("id", filter=Q(classification="WEAK")),
        usable=Count("id", filter=~Q(classification="REJECTED")),
        rejected=Count("id", filter=Q(classification="REJECTED")))
    trace = [[float(sample.longitude), float(sample.latitude)] for sample in
             survey.samples.exclude(classification="REJECTED").order_by("sequence")]
    matches = list(survey.segment_matches.select_related("segment", "reviewed_by"))
    analysis = analyse_survey_dry_run(survey) if survey.status in (
        PathSurvey.Status.COMPLETED, PathSurvey.Status.REVIEWED) else {"existing": [], "candidates": []}
    analysis_lookup = {str(item["segment"].pk): item for item in analysis["existing"]}
    locations = list(Location.objects.filter(
        representative_longitude__isnull=False, representative_latitude__isnull=False))
    candidates = []
    for candidate in analysis["candidates"]:
        midpoint = candidate["geometry"]["coordinates"][len(candidate["geometry"]["coordinates"]) // 2]
        nearest = min(((distance_metres(
            midpoint,
            (float(item.representative_longitude), float(item.representative_latitude)),
        ), item) for item in locations), key=lambda pair: pair[0], default=None)
        landmark = None
        if nearest and nearest[0] <= CANDIDATE_LANDMARK_CONTEXT_METRES:
            prefix = "Near" if nearest[0] <= NEARBY_CANDIDATE_LANDMARK_METRES else "Closest mapped place:"
            landmark = f"{prefix} {nearest[1].name} ({nearest[0]:.0f} m)"
        candidates.append({
            **candidate,
            "landmark": landmark,
            "near": landmark or "No nearby mapped place",
        })
    usable_points = [(float(sample.longitude), float(sample.latitude)) for sample in
                     survey.samples.exclude(classification="REJECTED").order_by("sequence")]
    primary_matches, diagnostic_matches = [], []
    for match in matches:
        nearby_count = sum(project_onto_segment(point, match.segment).distance_metres <= MATCH_DISTANCE_METRES
                           for point in usable_points)
        meaningful = (match.classification == SurveySegmentMatch.Classification.DISCREPANCY or
                      (float(match.coverage_percent) >= 1 and nearby_count >= 3))
        (primary_matches if meaningful else diagnostic_matches).append(match)
    match_lookup = {str(match.segment_id): match for match in matches}
    diagnostic_ids = {str(match.segment_id) for match in diagnostic_matches}
    network = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": segment.geometry,
         "properties": {"id": str(segment.id), "label": segment.label,
             "verification": segment.verification_state,
             "match_classification": (analysis_lookup[str(segment.id)]["classification"]
                                      if str(segment.id) in analysis_lookup else "UNOBSERVED"),
             "match_disposition": (match_lookup[str(segment.id)].disposition
                                   if str(segment.id) in match_lookup else "NONE"),
             "coverage_percent": (analysis_lookup[str(segment.id)]["best"].coverage_percent
                                  if str(segment.id) in analysis_lookup and
                                     analysis_lookup[str(segment.id)]["best"] else 0),
             "review_state": ("conflict" if (str(segment.id) in analysis_lookup and
                                  analysis_lookup[str(segment.id)].get("needs_review"))
                              else "verified" if segment.verification_state == VerificationState.FIELD_VERIFIED
                              else "supported" if (str(segment.id) in analysis_lookup and
                                  analysis_lookup[str(segment.id)]["classification"] == "STRONG")
                              else "conflict" if (str(segment.id) in analysis_lookup and
                                  analysis_lookup[str(segment.id)]["classification"] == "DISCREPANCY")
                              else "needs-confirmation" if (str(segment.id) in analysis_lookup and
                                  analysis_lookup[str(segment.id)]["classification"] in {"PARTIAL", "AMBIGUOUS"})
                              else "unobserved"),
             "diagnostic_only": str(segment.id) in diagnostic_ids}}
        for segment in WalkableSegment.objects.filter(is_active=True)
    ]}
    confirmation_segments = [{
        "segment": item["segment"],
        "classification": item["classification"],
        "coverage_percent": round(item.get("cumulative_coverage_percent", item["best"].coverage_percent), 1),
        "pass_count": len(item["passes"]),
    } for item in analysis["existing"]
        if item["best"] is not None
        and item["segment"].verification_state != VerificationState.FIELD_VERIFIED
        and item.get("needs_confirmation", item["classification"] in {
            "PARTIAL", "AMBIGUOUS", "DISCREPANCY",
        })]
    confirmation_candidates = [item for item in candidates if not item["confirmed"]]
    review_segments = [{
        "segment": item["segment"],
        "classification": item["classification"],
        "pass_count": len(item["passes"]),
    } for item in analysis["existing"]
        if item["segment"].verification_state == VerificationState.FIELD_VERIFIED
        and item.get("needs_review")]
    classification_counts = {choice: 0 for choice, _ in SurveySegmentMatch.Classification.choices}
    disposition_counts = {choice: 0 for choice, _ in SurveySegmentMatch.Disposition.choices}
    for match in matches:
        classification_counts[match.classification] += 1
        disposition_counts[match.disposition] += 1
    match_summary = {
        "total": len(matches),
        "classification": classification_counts,
        "disposition": disposition_counts,
        "reviewed": len(matches) - disposition_counts[SurveySegmentMatch.Disposition.PENDING],
        "pending": disposition_counts[SurveySegmentMatch.Disposition.PENDING],
    }
    return render(request, "editor/survey_detail.html", {"survey": survey, "can_review": can_review,
        "can_grant_verification": can_review and request.user.has_perm("routing.grant_field_verified"),
        "can_revoke_verification": can_review and request.user.has_perm("routing.revoke_field_verified"),
        "matches": primary_matches, "diagnostic_matches": diagnostic_matches, "sample_counts": counts,
        "match_summary": match_summary, "survey_network": network, "survey_trace": trace,
        "survey_candidates": {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": item["geometry"], "properties": {
                "id": item["id"], "length_metres": item["length_metres"],
                "pass_count": item["pass_count"], "status": item["status"], "near": item["near"],
                "review_url": reverse("editor:survey-candidate", args=(survey.pk, item["id"]))}}
            for item in candidates]},
        "candidates": candidates,
        "confirmation_candidates": confirmation_candidates,
        "confirmation_matches": confirmation_segments,
        "review_segments": review_segments,
        "evidence_summary": {
            "field_verified_campus": WalkableSegment.objects.filter(
                is_active=True,
                verification_state=VerificationState.FIELD_VERIFIED,
            ).count(),
            "sufficient": sum(item.get("evidence_sufficient", item["classification"] == "STRONG")
                              for item in analysis["existing"]),
            "needs_confirmation": len(confirmation_candidates) + len(confirmation_segments),
            "candidates": len(confirmation_candidates),
            "conflicts": sum(item["classification"] == "DISCREPANCY" for item in analysis["existing"]),
        },
        "can_create_candidate": all(request.user.has_perm(permission) for permission in (
            "routing.add_walkablenode", "routing.add_walkablesegment", "routing.change_walkablesegment")),
    })


@require_http_methods(["GET", "POST"])
@active_editor("routing.add_walkablesegment")
def survey_candidate(request, survey_id, candidate_id):
    survey = get_object_or_404(PathSurvey, pk=survey_id,
                               status__in=(PathSurvey.Status.COMPLETED, PathSurvey.Status.REVIEWED))
    if (not request.user.has_perm("routing.review_path_survey") or
            not request.user.has_perm("routing.add_walkablenode") or
            not request.user.has_perm("routing.change_walkablesegment")):
        raise PermissionDenied
    analysis = analyse_survey_dry_run(survey)
    candidate = next((item for item in analysis["candidates"] if item["id"] == candidate_id), None)
    if candidate is None:
        raise Http404("This derived survey candidate no longer exists.")
    preview = preview_candidate_graph_change(candidate)
    if request.method == "POST":
        if request.POST.get("confirm") != "yes":
            messages.error(request, "Explicitly confirm the graph change before applying it.")
        elif request.POST.get("candidate_fingerprint") != preview["candidate_fingerprint"]:
            messages.error(
                request,
                "This candidate changed since preview. Review the current geometry before confirming again.",
            )
        else:
            try:
                segment = create_candidate_path(survey=survey, candidate=candidate, actor=request.user)
            except ValidationError as error:
                messages.error(request, "; ".join(error.messages))
            else:
                messages.success(request, f"{candidate_id} created as {segment.get_verification_state_display()} geometry.")
                return redirect("editor:segment-edit", segment_id=segment.pk)
    return render(request, "editor/survey_candidate.html", {
        "survey": survey, "candidate": candidate, "preview": preview,
        "candidate_geojson": {"type": "Feature", "geometry": candidate["geometry"], "properties": {}},
    })


@require_POST
@active_editor("routing.conduct_path_survey")
def survey_samples(request, survey_id):
    survey = get_object_or_404(PathSurvey, pk=survey_id)
    try:
        body = json.loads(request.body)
        payloads = []
        for item in body.get("samples", []):
            payloads.append({"sequence": int(item["sequence"]), "captured_at": parse_datetime(item["captured_at"]),
                "longitude": item["longitude"], "latitude": item["latitude"], "accuracy": item["accuracy"],
                "speed": item.get("speed"), "heading": item.get("heading")})
        stored = store_samples(survey, payloads, request.user)
    except (ValueError, KeyError, TypeError, ValidationError) as error:
        return JsonResponse({"error": str(error)}, status=422)
    counts = survey.samples.aggregate(raw=Count("id"),
        usable=Count("id", filter=~Q(classification="REJECTED")),
        rejected=Count("id", filter=Q(classification="REJECTED")))
    trace = [[float(sample.longitude), float(sample.latitude)] for sample in
             survey.samples.exclude(classification="REJECTED").order_by("sequence")]
    return JsonResponse({"stored": len(stored), **counts, "trace": trace})


@require_POST
@active_editor("routing.conduct_path_survey")
def survey_timing(request, survey_id):
    survey = get_object_or_404(PathSurvey, pk=survey_id, owner=request.user, status=PathSurvey.Status.ACTIVE)
    try:
        seconds = max(0, int(json.loads(request.body).get("active_capture_seconds")))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "A valid active-capture duration is required."}, status=422)
    if seconds > survey.active_capture_seconds:
        survey.active_capture_seconds = seconds
    survey.active_capture_tracking_started = True
    survey.save(update_fields=("active_capture_seconds", "active_capture_tracking_started", "updated_at"))
    return JsonResponse({"active_capture_seconds": survey.active_capture_seconds})


@require_POST
@active_editor("routing.review_path_survey")
def survey_match_review(request, survey_id, match_id):
    match = get_object_or_404(SurveySegmentMatch, pk=match_id, survey_id=survey_id)
    action, reason = request.POST.get("action"), request.POST.get("reason", "")
    try:
        if action in ("grant", "revoke"):
            decide_verification(match, grant=action == "grant", actor=request.user, reason=reason)
        elif action == "review":
            record_match_review(
                match,
                disposition=request.POST.get("disposition"),
                actor=request.user,
                reason=reason,
            )
        else:
            raise ValidationError("Choose a valid evidence action.")
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(request, "Evidence decision recorded explicitly.")
    return redirect("editor:survey-detail", survey_id=survey_id)
