from dataclasses import dataclass

from .geometry import coordinates, length_metres


@dataclass(frozen=True)
class NetworkIssue:
    code: str
    object_id: str
    message: str


def inspect_network(segments):
    issues, seen = [], {}
    for segment in segments:
        try:
            points = tuple(coordinates(segment.geometry))
            length_metres(segment.geometry)
        except Exception as error:
            issues.append(NetworkIssue("malformed_geometry", str(segment.id), str(error)))
            continue
        if segment.start_node_id == segment.end_node_id:
            issues.append(NetworkIssue("self_edge", str(segment.id), "Segment connects a node to itself."))
        endpoint_key = (str(segment.start_node_id), str(segment.end_node_id))
        if segment.is_bidirectional:
            endpoint_key = tuple(sorted(endpoint_key))
            points = min(points, tuple(reversed(points)))
        key = (endpoint_key, segment.is_bidirectional, points)
        if key in seen:
            issues.append(NetworkIssue("duplicate_segment", str(segment.id), f"Duplicates segment {seen[key]}."))
        else:
            seen[key] = segment.id
    return issues
