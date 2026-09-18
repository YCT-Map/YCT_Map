import json
import uuid
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path


IMPORT_NAMESPACE = uuid.UUID("9fc40c2d-c970-46d2-94a8-05e02bcb67e2")
REJECTED_ACCESS = {"no", "private"}


def _inside(point, ring):
    x, y = point
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
        previous = current
    return inside


def _inside_runs(way, ring):
    runs = []
    current = []
    for node_id, geometry in zip(way["nodes"], way["geometry"]):
        item = (str(node_id), [float(geometry["lon"]), float(geometry["lat"])])
        if _inside(item[1], ring):
            current.append(item)
        else:
            if len(current) >= 2:
                runs.append(current)
            current = []
    if len(current) >= 2:
        runs.append(current)
    return runs


def build_records(snapshot, review, campus_boundary):
    approved = {int(item) for item in review["approved_way_ids"]}
    anchor_node_ids = {reference.removeprefix("node/") for reference in review.get("location_anchors", {}).values()}
    ring = campus_boundary["features"][0]["geometry"]["coordinates"][0]
    accepted = []
    rejected = []
    for way in snapshot.get("elements", []):
        tags = way.get("tags", {})
        reason = None
        if way.get("type") != "way" or int(way.get("id", 0)) not in approved:
            continue
        if tags.get("highway") == "construction" or tags.get("construction"):
            reason = "construction"
        elif tags.get("access") in REJECTED_ACCESS or tags.get("foot") == "no":
            reason = "access restriction"
        if reason:
            rejected.append({"way_id": way["id"], "reason": reason})
            continue
        runs = _inside_runs(way, ring)
        if not runs:
            rejected.append({"way_id": way["id"], "reason": "outside campus boundary"})
            continue
        accepted.append((way, runs))

    usage = Counter()
    for _, runs in accepted:
        for run in runs:
            usage.update({node_id for node_id, _ in run})

    node_records = {}
    segment_records = []
    for way, runs in accepted:
        tags = way.get("tags", {})
        for run_number, run in enumerate(runs):
            decision_indices = {0, len(run) - 1}
            decision_indices.update(index for index, (node_id, _) in enumerate(run) if usage[node_id] > 1)
            decision_indices.update(index for index, (node_id, _) in enumerate(run) if node_id in anchor_node_ids)
            ordered = sorted(decision_indices)
            for index in ordered:
                node_id, coordinates = run[index]
                node_records.setdefault(node_id, {
                    "id": uuid.uuid5(IMPORT_NAMESPACE, f"osm-node:{node_id}"),
                    "label": f"OSM-derived node {node_id}",
                    "longitude": Decimal(f"{coordinates[0]:.6f}"),
                    "latitude": Decimal(f"{coordinates[1]:.6f}"),
                    "source_reference": f"node/{node_id}",
                })
            for part_number, (start_index, end_index) in enumerate(zip(ordered, ordered[1:])):
                if end_index <= start_index:
                    continue
                start_node = run[start_index][0]
                end_node = run[end_index][0]
                reference = f"way/{way['id']}:{run_number}:{part_number}:{start_node}-{end_node}"
                segment_records.append({
                    "id": uuid.uuid5(IMPORT_NAMESPACE, reference),
                    "label": f"OSM-derived way {way['id']}",
                    "start_reference": f"node/{start_node}",
                    "end_reference": f"node/{end_node}",
                    "geometry": {"type": "LineString", "coordinates": [point for _, point in run[start_index:end_index + 1]]},
                    "is_bidirectional": tags.get("oneway:foot") != "yes",
                    "source_reference": f"way/{way['id']}",
                    "source_version": way.get("version"),
                    "source_timestamp": datetime.fromisoformat(way["timestamp"].replace("Z", "+00:00")) if way.get("timestamp") else None,
                })
    return {"nodes": list(node_records.values()), "segments": segment_records, "rejected": rejected}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
