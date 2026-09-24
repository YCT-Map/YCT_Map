from dataclasses import dataclass

from django.core.exceptions import ValidationError

from locations.models import Entrance, InternalPlace, Location
from .models import EntranceNetworkAnchor, LocationNetworkAnchor


@dataclass(frozen=True)
class DestinationResolution:
    key: str
    kind: str
    destination: object
    location: Location
    entrance: Entrance | None
    node: object | None
    routing_available: bool
    unavailable_reason: str
    used_legacy_anchor: bool = False

    @property
    def name(self):
        return self.destination.name


def parse_destination_key(value):
    raw = str(value).strip()
    if raw.startswith("internal:"):
        return "internal", raw.removeprefix("internal:")
    if raw.startswith("location:"):
        return "location", raw.removeprefix("location:")
    return "location", raw


def _unavailable(key, kind, destination, location, reason, entrance=None):
    return DestinationResolution(key, kind, destination, location, entrance, None, False, reason)


def resolve_destination(value, *, allow_legacy=True):
    kind, identifier = parse_destination_key(value)
    try:
        if kind == "internal":
            destination = InternalPlace.objects.select_related("location", "floor", "routing_entrance").get(
                id=identifier,
                publication_status=Location.PublicationStatus.PUBLISHED,
                location__publication_status=Location.PublicationStatus.PUBLISHED,
            )
            location = destination.location
            key = f"internal:{destination.id}"
            if not destination.floor_id or not destination.floor.is_active:
                return _unavailable(key, kind, destination, location, "Floor information is incomplete.")
            if destination.routing_entrance_id:
                entrance = destination.routing_entrance
                if entrance.location_id != location.id:
                    return _unavailable(key, kind, destination, location, "The selected entrance belongs to another place.")
                if not entrance.is_active:
                    return _unavailable(key, kind, destination, location, "The selected entrance is inactive.", entrance)
            else:
                entrance = location.entrances.filter(is_active=True, is_primary=True).first()
        else:
            destination = Location.objects.get(id=identifier, publication_status=Location.PublicationStatus.PUBLISHED)
            location = destination
            key = f"location:{destination.id}"
            entrance = location.entrances.filter(is_active=True, is_primary=True).first()
    except (Location.DoesNotExist, InternalPlace.DoesNotExist, ValueError, ValidationError) as error:
        raise ValidationError("Unknown or unavailable destination.") from error

    if not entrance:
        if allow_legacy:
            legacy = LocationNetworkAnchor.objects.filter(
                location=location, is_active=True, node__is_active=True,
            ).select_related("node").first()
            if legacy:
                return DestinationResolution(key, kind, destination, location, None, legacy.node, True, "", True)
        return _unavailable(key, kind, destination, location, "No active primary entrance has been configured.")
    anchor = EntranceNetworkAnchor.objects.filter(
        entrance=entrance, is_active=True, node__is_active=True,
    ).select_related("node").first()
    if anchor:
        return DestinationResolution(key, kind, destination, location, entrance, anchor.node, True, "")
    if allow_legacy:
        legacy = LocationNetworkAnchor.objects.filter(
            location=location, is_active=True, node__is_active=True,
        ).select_related("node").first()
        if legacy:
            return DestinationResolution(key, kind, destination, location, entrance, legacy.node, True, "", True)
    return _unavailable(key, kind, destination, location, "The arrival entrance is not connected to the walkable network.", entrance)


def destination_summary(resolution):
    summary = {
        "key": resolution.key,
        "type": resolution.kind,
        "id": str(resolution.destination.id),
        "name": resolution.name,
        "parent": {"id": str(resolution.location.id), "name": resolution.location.name},
        "routing_available": resolution.routing_available,
        "routing_unavailable_reason": resolution.unavailable_reason,
    }
    if resolution.entrance:
        summary["arrival_entrance"] = {"id": str(resolution.entrance.id), "name": resolution.entrance.name}
    if resolution.kind == "internal":
        internal = resolution.destination
        summary.update({
            "floor": internal.floor.label if internal.floor_id else "",
            "room_code": internal.room_code,
            "wing_section": internal.wing_section,
            "direction_note": internal.direction_note,
        })
    return summary
