# Routing — YCT Map

## Status

```
Current phase:     PHASE 4 SPRINT 004 — PHYSICAL OWNER ACCEPTANCE PENDING
Implementation:    ENTRANCE-AWARE ROUTING, LIVE NAVIGATION, SURVEY EVIDENCE AND VERIFICATION WORKFLOWS IMPLEMENTED
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

Phase 2 implements static/manual routing. Live-position navigation remains Phase 3 work.

---

## Demo Data for Routing

The routing system must work correctly against demonstration data before real campus paths are field-verified.

Demo paths must be clearly labelled DEMO in the data model.

The primary development network is now built from a reviewed OpenStreetMap/Overpass snapshot: 47 YCT Map-owned nodes and 54 segments derived from 30 campus highway ways. Every record is `UNVERIFIED`; visual plausibility is not evidence of pedestrian access, safety or field verification. The old synthetic topology remains only for deterministic automated tests.

The importer preserves OSM way/node references, source way version and timestamp, clips processing to vertices inside the approved campus polygon, splits ways at endpoints, shared OSM nodes and reviewed arrival nodes, and never joins un-noded geometric crossings. Vehicle `oneway=yes` does not restrict walking unless `oneway:foot=yes` is present.

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
- Reliable live geolocation uses a directional triangle when a fresh absolute device heading is available, falls back to trustworthy movement heading when the device heading is stale/unavailable, and uses a dot when neither direction is trustworthy.
- Heading or orientation must be shown only when reliable live-position and heading information exists.

The geographic convention is 0° north, 90° east, 180° south and 270° west. Absolute orientation is converted from device coordinates with screen orientation applied once. The intrinsic triangle points up/north at zero and MapLibre's map-aligned rotation accounts for current map bearing; application code does not apply a second bearing correction or a visual 180° offset.

These approved Sprint 003 presentation requirements are implemented separately from the Sprint 002 technical inspector.

Sprint 003 implements them with a static blue `S` start marker, a larger red `D` destination marker and a blue cased route. No marker rotates or claims live position. Route bounds use all route coordinates with mobile/desktop panel-aware padding and a short-route zoom cap.

The public route contract accepts stable location UUIDs and intentionally returns only route geometry, endpoint names, distance, approximate ETA and verification context. Graph IDs and algorithm internals remain private. DEBUG topology tools are separate and collapsed by default.

The normal-user controller owns explicit `browsing`, `destination-selected`, `choosing-origin` and `route-available` states. A Directions action changes state atomically before the destination panel is released, preventing a fragile transition from leaving no visible owner of the interface.

The OSM realism pass did not replace or repair A*. A* was already returning the shortest route in the supplied graph. Replacing unrealistic synthetic geometry with a more plausible reviewed OSM-derived graph improved visible routes because route quality depends on input topology as well as algorithm correctness.

Active manual shortcut segments participate through the same adjacency graph as OSM-derived segments. A* may select a shortcut only when its endpoints genuinely connect and its geometry-derived cost produces the shortest valid route; disconnected and inactive geometry cannot create a jump. Distance, ETA and route verification context are derived from the exact selected segment sequence.

## Phase 4 Entrance and Internal-Destination Contract

The owner-approved Phase 4 specification separates an outdoor place's representative map point from its routing entrances. Sprint 002 implements multiple named entrances with at most one active primary/default entrance. An internal destination routes through its active same-parent entrance when selected, otherwise through the parent's primary entrance. It does not create indoor route geometry.

Publication is not a routing assertion. Published outdoor and internal destinations remain searchable when entrance or anchor resolution is incomplete. Their public contract reports `routing_available=false` with a specific reason and the client disables Directions. Cross-parent, inactive and malformed relationships are rejected rather than silently falling back. A route-ready destination requires a valid active arrival entrance and active graph anchor; verification remains independent.

### Exact Entrance Arrival Connector

`EntranceNetworkAnchor` may store an editor-approved GeoJSON connector from its active `WalkableNode` to the exact physical Entrance coordinate. The editor sees the entrance, selected node, graph and proposed connector, may add intermediate bend points, and must confirm explicitly. A straight proposal is never automatically treated as walkable.

Server validation requires a finite local LineString whose first coordinate exactly matches the selected node and whose last coordinate exactly matches the Entrance. Distance is derived from every geometry leg. A* remains unchanged: after graph routing succeeds, the destination connector is appended, or the reversed connector is prepended for a supported entrance origin. Total distance, approximate ETA, destination marker and `fitBounds` use the composed route.

Existing anchors with no connector remain functional through explicit legacy node-only behavior; no migration fabricates geometry. The current connector starts at an existing graph node, so a mid-segment real-world approach can still produce avoidable backtracking. Segment-aware entrance attachment through a safe transactional split is future work.

### Internal-Place Handoff

An `InternalPlace` uses its configured active same-parent routing entrance or falls back to the parent Location's active primary entrance. YCT Map routes outdoors only. The compact and expanded route UI preserve the internal name, floor, room/code, wing and `direction_note`, while arrival language names the building Entrance. No route response claims indoor geometry or arrival at the room.

## Real Network Construction and Validation

### Phase 4 Sprint 003 Path Editing Boundary

Authenticated Editors may add/edit `UNVERIFIED` nodes and segments without changing the graph model used by A*. Connected nodes are coordinate-locked because an uncoordinated drag would invalidate attached LineString endpoints. Segment deactivation warnings report concrete remaining endpoint degree and active entrance/location anchors; stored data cannot truthfully claim whether a segment is part of a currently displayed route.

Segment splitting is explicit and transactional: lock the active original, validate a point within five metres and away from endpoints, create one UNVERIFIED node and two endpoint-consistent UNVERIFIED segments, then retain the original as inactive history. No automatic OSM synchronization or field-verification promotion occurs.

### Phase 4 Sprint 004 Survey and Verification Boundary

The phone records explicitly started private evidence; it does not author routing geometry. Samples at up to 25 m accuracy are generally usable, 25–50 m samples are weak, and samples over 50 m are rejected from matching. Near-duplicates, stationary points and implausible jumps are retained with classification but excluded from candidate analysis.

Usable traces from finalized `COMPLETED` and `REVIEWED` surveys are compared with active segments as chronological corridor passes rather than as a whole-survey nearby-sample ratio. High callback frequency never creates extra passes, and rejected samples, unfinished surveys and abandoned surveys do not contribute. A supporting pass requires at least five usable points, meaningful segment coverage, median offset at most 5 m, 90th-percentile offset at most 9 m, median accuracy at most 8 m, coherent movement along the segment and no competing-geometry ambiguity. Automatic promotion additionally requires at least two independent supporting passes whose merged intervals reach at least 80% coverage without a material unsupported gap.

Only an explicit future survey-completion POST evaluates segments observed by that new survey for one-way `UNVERIFIED` to `FIELD_VERIFIED` promotion. Startup, deployment, review GETs and dry runs are read-only. A human `REJECTED` disposition removes that survey's match from automatic support for the segment; `DISCREPANCY_CONFIRMED` blocks promotion and creates a review item. Later weak or conflicting evidence never auto-revokes `FIELD_VERIFIED`.

Evidence beyond the active graph is grouped into plausible continuous candidate runs only when accuracy, point count, displacement, length, straightness, time/step continuity and graph clearance are adequate. Candidates remain derived review data; human labels such as `C1` are presentation only, while a direction-independent geometry fingerprint provides stable geometry identity and a separate evidence-bound confirmation token protects preview-to-POST state. Explicit authorized POST approval recomputes current evidence, previews endpoint reuse/node creation/safe splitting and applies the change transactionally. Accuracy-plausible parallel traces are not merged merely to create confirmation. A single pass creates `UNVERIFIED` geometry; at least two genuinely separate passes meeting the same strict quality profile are required before explicitly approved new geometry may start `FIELD_VERIFIED`. Otherwise a later qualifying pass beginning after graph creation is required, and the segment remains in Needs Confirmation until then.

Dedicated permissions still govern manual grant/revoke and reviewer-only decisions. Reviewer-only disposition, reason, latest actor and latest time are stored atomically; historical null actor/time remains identifiable rather than fabricated. An automatic cumulative existing-geometry grant records a verification-history entry with a null actor and an explicit evidence-based reason. Material segment mutation invalidates the current state and preserves the prior decision record. Deactivation alone does not destroy verification because it does not alter geometry; later reactivation may retain it. Raw survey evidence and candidate paths are absent from public map, search and routing contracts.

Existing OSM/OpenFreeMap-visible pathways may be used as reference input when constructing YCT Map's real walkable network; they do not automatically become routing edges. YCT Map must own, import or create explicit graph geometry, retain editor review, and keep field verification separate.

Incorrect or missing paths must remain editable. Future Path Survey Mode may help verify and refine them. Editor/path validation should flag ordinary outdoor segments intersecting building footprints for review while allowing deliberate, reviewed exceptions for genuine passages or corridors.

## Phase 3 Live-Location Boundary

Sprint 001 keeps accepted browser positions transient and client-side. It does not pass arbitrary GPS coordinates into A* or create temporary graph nodes. Manual location anchors remain the only public route origins.

Sprint 002 implements live-origin matching by projecting an accepted coordinate onto every leg of eligible segment geometry. It prefers matches within 25 m, permits 25–40 m only with accuracy of 25 m or better, and rejects matches beyond 40 m. A request-local virtual node connects to the matched segment endpoints according to segment direction; no node, segment, coordinate history or breadcrumb is persisted.

The measured blue position and the hollow network-match marker are deliberately separate. No straight visual connector is invented. During an active live route, the browser projects accepted samples onto the complete authoritative route geometry, stabilizes backward/noisy progress, calculates remaining distance along the route, and derives ETA from a rolling median of plausible walking samples when sufficient evidence exists. The map slices a presentation copy at that trusted geographic progress: a thin grey-blue line shows the completed portion and the strong cased blue line shows the remaining route. Uncertain or off-route evidence freezes this visual progress; it is never calculated from raw marker position. Manual routes remain complete. Otherwise the documented 1.35 m/s fallback remains explicit.

Sprint 002 is OWNER ACCEPTED as `SIMULATED LIVE NAVIGATION VERIFIED`. Owner review covered safe/unsafe snapping, live-origin routing, route progress, remaining distance and personal-pace ETA. Stationary and arrival transitions are verified by deterministic tests only. Physical-device navigation, off-route detection and automatic rerouting remain unverified or unimplemented.

## Sprint 003 Off-Route Detection and Controlled Rerouting

The browser now evaluates location quality separately from route-match quality. Accuracy worse than 25 m creates an uncertain state and cannot contribute off-route evidence. For reliable positions, an accuracy-aware route corridor classifies samples as following, uncertain or displaced. Three consecutive displaced samples spanning at least eight seconds, with credible movement or twelve seconds of sustained displacement, confirm departure.

Confirmed departure reuses the protected live-origin POST contract once. Django repeats safe network matching, creates an ephemeral origin and runs A* to the unchanged destination. A successful replacement resets route-specific progress, stationary and arrival state while retaining valid personal walking-pace samples. A ten-second stabilization window, 30-second cooldown and 20 m movement gate prevent request storms. Failure retains the previous route as faded reference and offers an explicit retry.

The full route remains authoritative for tracking, off-route detection, ETA and arrival even while its presentation is progressively sliced. A successful reroute replaces that full geometry and resets both completed and remaining presentation sources; a failed reroute retains the prior geometry. The accepted GPS marker is never snapped to the route projection.

Arrival takes precedence, backtracking inside the corridor remains on-route, and poor GPS freezes trustworthy progress rather than producing a false reroute. Physical-device rerouting and the OSM-derived graph remain unverified.

Sprint 003 is OWNER ACCEPTED as `SIMULATED REROUTING VERIFIED`. Owner review covered the checking state, controlled route replacement, destination preservation, continued navigation progress and non-hijacking camera behavior. The detailed timing, cooldown, poor-GPS, failure and arrival branches retain deterministic automated-test verification rather than being described as manually owner-verified.

Phase 3 is OWNER ACCEPTED / COMPLETE. Sprint 004 preserved manual routing and active route state while contribution/mobile bottom sheets temporarily own the foreground. Contribution approval never edits routing geometry or destination anchors. Physical-device navigation/rerouting, the OSM-derived network and all campus paths remain unverified in the field.

---

## Field-Test Route-Setup Stabilization

The public client preserves the live-origin matching limits described above. If route setup returns `NO_SAFE_NETWORK_MATCH` or `INSUFFICIENT_ACCURACY`, it may retry only when the existing location controller supplies a newer accepted position that still satisfies the 40 m client usability contract. Recovery performs at most three total attempts within ten seconds, never polls and never overlaps requests. All other error codes stop immediately. Changing origin or destination, cancelling, or closing aborts pending setup.

This recovery addresses short-lived mismatch between an accepted display position and network matching without widening backend safety thresholds, inventing connectors, or creating a second GPS pipeline.

## Not In V1

- Multi-stop routing
- Accessibility-optimized routing (may be V2 candidate)
- Indoor routing
- Navigation outside campus boundaries
- Voice turn-by-turn
