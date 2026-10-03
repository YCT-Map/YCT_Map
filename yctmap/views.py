from django.http import JsonResponse
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse


def csrf_recovery_url(request):
    """Return a stable GET page for a rejected editor POST.

    A CSRF failure can occur after a mobile browser restores an old form. The
    rejected action URL is often POST-only, so linking back to request.path
    would leave the user on a 405 (or a stale nested-object 404).
    """
    match = getattr(request, "resolver_match", None)
    view_name = getattr(match, "view_name", "") or ""
    kwargs = getattr(match, "kwargs", {}) or {}
    if not view_name.startswith("editor:"):
        return reverse("locations:map")

    from contributions.models import Contribution
    from locations.models import Entrance, Floor, InternalPlace, Location
    from routing.models import PathSurvey, WalkableNode, WalkableSegment

    user = request.user
    place_id = kwargs.get("place_id")
    entrance_id = kwargs.get("entrance_id")
    floor_id = kwargs.get("floor_id")
    internal_id = kwargs.get("internal_id")
    node_id = kwargs.get("node_id")
    segment_id = kwargs.get("segment_id")
    contribution_id = kwargs.get("contribution_id")
    survey_id = kwargs.get("survey_id")
    place_exists = place_id and Location.objects.filter(pk=place_id).exists()
    entrance_exists = entrance_id and place_exists and Entrance.objects.filter(
        pk=entrance_id, location_id=place_id,
    ).exists()
    floor_exists = floor_id and place_exists and Floor.objects.filter(
        pk=floor_id, location_id=place_id,
    ).exists()
    internal_exists = internal_id and place_exists and InternalPlace.objects.filter(
        pk=internal_id, location_id=place_id,
    ).exists()

    def allowed(*permissions):
        return user.is_authenticated and any(user.has_perm(permission) for permission in permissions)

    def editor_url(name, **url_kwargs):
        return reverse(f"editor:{name}", kwargs=url_kwargs or None)

    try:
        if view_name == "editor:place-create" and allowed("locations.add_location"):
            return editor_url("place-create")
        if (view_name == "editor:place-detail" and place_exists and
                allowed("locations.view_location", "locations.change_location")):
            return editor_url("place-detail", place_id=place_id)
        if (view_name in {"editor:place-verification", "editor:place-archive", "editor:place-reactivate"}
                and place_exists and allowed("locations.change_location")):
            return editor_url("place-detail", place_id=place_id)
        if (view_name == "editor:entrance-create" and place_exists and
                allowed("locations.add_entrance")):
            return editor_url("entrance-create", place_id=place_id)
        if view_name in {
            "editor:entrance-edit",
            "editor:entrance-verification",
            "editor:entrance-connection-update",
        } and entrance_exists and allowed("locations.change_entrance"):
            return editor_url("entrance-edit", place_id=place_id, entrance_id=entrance_id)
        if view_name == "editor:floor-create" and place_exists and allowed("locations.add_floor"):
            return editor_url("floor-create", place_id=place_id)
        if view_name == "editor:floor-edit" and floor_exists and allowed("locations.change_floor"):
            return editor_url("floor-edit", place_id=place_id, floor_id=floor_id)
        if view_name == "editor:internal-create" and place_exists and allowed("locations.add_internalplace"):
            return editor_url("internal-create", place_id=place_id)
        if (view_name == "editor:internal-edit" and internal_exists and
                allowed("locations.change_internalplace")):
            return editor_url("internal-edit", place_id=place_id, internal_id=internal_id)

        if view_name == "editor:contribution-detail" and allowed("contributions.resolve_contribution"):
            contribution_exists = contribution_id and Contribution.objects.filter(
                pk=contribution_id,
                status=Contribution.Status.APPROVED,
            ).exists()
            if contribution_exists:
                return editor_url("contribution-detail", contribution_id=contribution_id)
            return editor_url("contribution-list")

        if view_name == "editor:node-create" and allowed("routing.add_walkablenode"):
            return editor_url("node-create")
        if (view_name == "editor:node-edit" and node_id and
                WalkableNode.objects.filter(pk=node_id).exists() and
                allowed("routing.change_walkablenode")):
            return editor_url("node-edit", node_id=node_id)
        if view_name == "editor:segment-create" and allowed("routing.add_walkablesegment"):
            return editor_url("segment-create")
        if (view_name in {"editor:segment-edit", "editor:segment-split"} and segment_id and
                WalkableSegment.objects.filter(pk=segment_id).exists() and
                allowed("routing.change_walkablesegment")):
            return editor_url("segment-edit", segment_id=segment_id)

        survey = PathSurvey.objects.filter(pk=survey_id).first() if survey_id else None
        may_review_surveys = allowed("routing.review_path_survey")
        may_access_survey = bool(survey and (
            may_review_surveys or (
                allowed("routing.conduct_path_survey") and survey.owner_id == user.pk
            )
        ))
        if view_name == "editor:survey-create" and allowed("routing.conduct_path_survey"):
            return editor_url("survey-list")
        if view_name in {
            "editor:survey-detail",
            "editor:survey-samples",
            "editor:survey-timing",
            "editor:survey-match-review",
            "editor:survey-candidate",
        } and may_access_survey:
            return editor_url("survey-detail", survey_id=survey_id)

        # A stale nested object may be gone. Prefer a parent/collection only
        # when this account can actually open it; otherwise use the public map.
        if place_exists and allowed("locations.view_location", "locations.change_location"):
            return editor_url("place-detail", place_id=place_id)
        if allowed("locations.view_location"):
            return editor_url("place-list")
        if allowed("routing.view_walkablesegment"):
            return editor_url("path-list")
        if allowed("routing.conduct_path_survey", "routing.review_path_survey"):
            return editor_url("survey-list")
        if allowed("contributions.resolve_contribution"):
            return editor_url("contribution-list")
    except NoReverseMatch:
        pass
    return reverse("locations:map")


def csrf_failure(request, reason=""):
    """Retain a secure 403 while giving field users a recoverable next action."""
    response = render(request, "csrf_failure.html", {
        "recovery_url": csrf_recovery_url(request),
    }, status=403)
    response.headers["Cache-Control"] = "no-store, private"
    return response


def health_check(request):
    """Lightweight process health endpoint for the hosting platform."""
    return JsonResponse({"status": "ok"})
