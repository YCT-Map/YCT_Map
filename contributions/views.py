import hashlib
import json
import uuid
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from locations.models import Location
from .models import Contribution


ALLOWED_FIELDS = {"request_id", "type", "target_location", "proposed_name", "proposed_category",
                  "description", "context", "proposed_point", "website"}
SESSION_LIMIT = 3
SESSION_WINDOW_SECONDS = 600
ABUSE_LIMIT = 30
ABUSE_WINDOW_SECONDS = 86_400
COORDINATE_QUANTUM = Decimal("0.000001")


def _counter_allowed(key, limit, timeout):
    if cache.add(key, 1, timeout=timeout):
        return True
    try:
        return cache.incr(key) <= limit
    except ValueError:
        cache.set(key, 1, timeout=timeout)
        return True


def _session_key(request):
    if not request.session.session_key:
        request.session.create()
    return f"contribution:accepted:{request.session.session_key}"


def _accepted_allowed(request):
    return int(cache.get(_session_key(request), 0)) < SESSION_LIMIT


def _record_accepted(request):
    _counter_allowed(_session_key(request), SESSION_LIMIT, SESSION_WINDOW_SECONDS)


def _abuse_allowed(request):
    remote_address = request.META.get("REMOTE_ADDR", "unknown")
    digest = hashlib.sha256(f"{settings.SECRET_KEY}:{remote_address}".encode()).hexdigest()[:24]
    return _counter_allowed(f"contribution:abuse:{digest}", ABUSE_LIMIT, ABUSE_WINDOW_SECONDS)


def _error(message, code, status=400, fields=None):
    payload = {"error": message, "code": code}
    if fields:
        payload["fields"] = fields
    return JsonResponse(payload, status=status)


@require_POST
def submit_contribution(request):
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict) or set(payload) - ALLOWED_FIELDS:
            return _error("The contribution payload is invalid.", "VALIDATION_ERROR")
        request_id = uuid.UUID(str(payload.get("request_id", "")))
    except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
        return _error("The contribution payload is invalid.", "VALIDATION_ERROR")

    existing = Contribution.objects.filter(request_id=request_id).first()
    if existing:
        return JsonResponse({"id": str(existing.id), "status": existing.status, "duplicate_request": True})

    if not _abuse_allowed(request):
        response = _error("Too many requests. Please wait before trying again.", "RATE_LIMITED", status=429)
        response.headers["Retry-After"] = str(ABUSE_WINDOW_SECONDS)
        return response

    if str(payload.get("website", "")).strip():
        return JsonResponse({"id": str(request_id), "status": Contribution.Status.PENDING,
                             "message": "Thank you. Your submission will be reviewed."}, status=201)

    contribution_type = str(payload.get("type", ""))
    if contribution_type not in Contribution.Type.values:
        return _error("Choose a valid contribution type.", "INVALID_TYPE", fields={"type": ["Invalid type."]})

    target = None
    target_id = payload.get("target_location")
    if target_id:
        try:
            target = Location.objects.get(pk=target_id, publication_status=Location.PublicationStatus.PUBLISHED)
        except (Location.DoesNotExist, ValueError, ValidationError):
            return _error("The selected place is unavailable.", "INVALID_TARGET",
                          fields={"target_location": ["Choose an active place."]})

    latitude = longitude = None
    point = payload.get("proposed_point")
    if point is not None:
        try:
            if not isinstance(point, dict) or set(point) != {"latitude", "longitude"}:
                raise ValueError
            latitude = Decimal(str(point["latitude"]))
            longitude = Decimal(str(point["longitude"]))
            if not latitude.is_finite() or not longitude.is_finite():
                raise ValueError
            latitude = latitude.quantize(COORDINATE_QUANTUM)
            longitude = longitude.quantize(COORDINATE_QUANTUM)
        except (InvalidOperation, TypeError, ValueError, KeyError):
            return _error("The selected map point could not be submitted. Please choose the point again.",
                          "INVALID_COORDINATE", fields={"proposed_point": ["Choose a valid map point."]})

    contribution = Contribution(
        request_id=request_id, contribution_type=contribution_type, target_location=target,
        proposed_name=str(payload.get("proposed_name", "")), proposed_category=str(payload.get("proposed_category", "")),
        description=str(payload.get("description", "")), context=str(payload.get("context", "")),
        proposed_latitude=latitude, proposed_longitude=longitude,
    )
    try:
        contribution.full_clean()
    except ValidationError as error:
        coordinate_fields = {"proposed_latitude", "proposed_longitude"}
        if coordinate_fields.intersection(error.message_dict):
            return _error("The selected map point could not be submitted. Please choose the point again.",
                          "INVALID_COORDINATE", status=422,
                          fields={"proposed_point": ["Choose a valid map point."]})
        return _error("Please correct the highlighted fields.", "VALIDATION_ERROR", status=422,
                      fields=error.message_dict)
    if not _accepted_allowed(request):
        response = _error("Too many submissions. Please wait before trying again.", "RATE_LIMITED", status=429)
        response.headers["Retry-After"] = str(SESSION_WINDOW_SECONDS)
        return response
    contribution.save()
    _record_accepted(request)
    return JsonResponse({"id": str(contribution.id), "status": contribution.status,
        "message": "Thank you. Your submission will be reviewed before it can affect YCT Map."}, status=201)
