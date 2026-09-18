# Routing — YCT Map

## Status

```
Current phase:     PHASE 2 / SPRINT 002
Implementation:    SPRINT 002 OWNER ACCEPTED; USER-FACING ROUTE UX NEXT
```

This document records the approved routing behavior for YCT Map.

---

## Scope

Routing applies **only within YabaTech campus boundaries**.

YCT Map is not a city-wide navigation service and does not route outside the campus.

---

## Approved Routing Behavior

- Routes are visualized on the map.
- Route distance is displayed (calculated from geographic geometry — not manually entered).
- Estimated walking time is displayed.
- Basic written / step-by-step guidance is provided.
- Live position tracking is active during navigation when GPS is available.
- If a user materially departs the planned route, rerouting is triggered.
- GPS noise must not trigger unnecessary rerouting. A meaningful position departure threshold must be defined.

---

## Starting Point

- If GPS is active: route is calculated from the user's current position.
- If GPS is unavailable or denied: the user chooses a starting point manually (search or map tap).

---

## Path Data

- Walkable paths within YCT Map are maintained as geographic linestrings.
- Path distances are derived from geographic geometry.
- Paths must not cross buildings, walls, fences or restricted spaces.
- Missing paths can be added to YCT Map without requiring upstream OpenStreetMap edits.

---

## Routing Algorithm

Use a campus network graph with Dijkstra / A* over YCT Map's connected walkable-path linestring geometry (DEC-T05).

Walking ETA uses `1.35 m/s` as the current default speed assumption and must be presented as approximate (DEC-T14).

The default is a fallback rather than the final live-navigation mechanism. Phase 3 may derive a smoothed user-specific walking speed only from reliable movement updates, excluding GPS outliers and stationary periods, and must fall back to `1.35 m/s` when personal speed is not reliable.

Routing remains outside Phase 1 Sprint 001.

---

## Demo Data for Routing

The routing system must work correctly against demonstration data before real campus paths are field-verified.

Demo paths must be clearly labelled DEMO in the data model.

The current purple network is synthetic and geographically unverified. Some segments do not correspond to real campus walkways. This is a known fixture limitation, not a claim about campus access and not a routing-engine defect. Real paths must be populated and field-verified later.

## Sprint 001 Foundation

- `WalkableNode` persists junction coordinates, active state and controlled verification state.
- `WalkableSegment` persists endpoint references, directionality and GeoJSON `LineString` geometry.
- Length is calculated dynamically across every geometry leg; it is never manually stored.
- `build_graph()` converts active records into immutable adjacency arcs and reverses bidirectional geometry.
- Diagnostics detect malformed geometry, self-edges and exact duplicate/reverse-duplicate segments.
- A DEBUG-only endpoint and dashed overlay expose DEMO topology for inspection, not as a calculated route.
- A* route selection, destination snapping, route results, distance totals and ETA remain deferred.

## Sprint 002 Route Calculation

- Pure A* uses geometry-derived arc distance as `g`, Haversine distance to the goal as admissible `h`, and prioritizes `f = g + h`.
- Predecessor arcs reconstruct ordered nodes, segments and traversal-oriented geometry.
- Geometry retains intermediate vertices and removes only duplicated shared junction coordinates.
- `RouteResult` is immutable; invalid nodes, missing anchors and unreachable routes have distinct errors.
- Same-origin routing succeeds with zero distance, no segments and zero ETA.
- `LocationNetworkAnchor` connects a DEMO destination to one node without making `Location` graph topology.
- Core routing remains independently callable with node IDs.
- A DEBUG-only inspector highlights the selected subset separately from the full purple network and reports approximate distance/ETA.

## Origin and Destination Presentation

- A manual or otherwise static origin must use a clear start marker that does not imitate live GPS.
- A destination must use a clear red destination indicator.
- When Phase 3 introduces reliable live geolocation, the user's actual position may use a directional triangle or chevron.
- Heading or orientation must be shown only when reliable live-position and heading information exists.

These are approved Sprint 003 presentation requirements. They are not implemented by the Sprint 002 technical inspector.

## Real Network Construction and Validation

Existing OSM/OpenFreeMap-visible pathways may be used as reference input when constructing YCT Map's real walkable network; they do not automatically become routing edges. YCT Map must own, import or create explicit graph geometry, retain editor review, and keep field verification separate.

Incorrect or missing paths must remain editable. Future Path Survey Mode may help verify and refine them. Editor/path validation should flag ordinary outdoor segments intersecting building footprints for review while allowing deliberate, reviewed exceptions for genuine passages or corridors.

---

## Not In V1

- Multi-stop routing
- Accessibility-optimized routing (may be V2 candidate)
- Indoor routing
- Navigation outside campus boundaries
- Voice turn-by-turn
