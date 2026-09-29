# Architecture — YCT Map

## Status

```
Current phase:         PHASE 4 — EDITOR & MAPPING TOOLS
Application code:      SPRINTS 001–003 OWNER ACCEPTED; SPRINT 004 TECHNICALLY COMPLETE / PHYSICAL ACCEPTANCE PENDING
```

This document records approved architectural decisions and expected system design.

Phase 4 campus-place and editor modeling is governed by [`../phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md`](../phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md). Sprint 002 implements its entrance, floor and internal-place foundation. Publication, verification and routing readiness are independent concepts.

Sections are clearly marked CURRENT or PLANNED. Nothing is described as implemented unless it is.

---

## System Overview

YCT Map is a web-based application consisting of:

| Layer | Description | Status |
|-------|-------------|--------|
| Frontend | Django templates, CSS and modular JavaScript; public map plus trusted editor | CURRENT — Phase 4 |
| Backend API | Search, destination, anchored/live routes and anonymous contributions | CURRENT — Phase 4 |
| Database | SQLite locally; campus places, entrances/internal places, contributions and routing graph | CURRENT — Phase 4 |
| Authentication | Django sessions and least-privilege Editor permissions | CURRENT — Phase 4 |
| Map tiles | OpenFreeMap Liberty rendered with MapLibre GL JS | CURRENT |

---

## Frontend

**Status: CURRENT — PHASE 4 PRE-CLOSEOUT**

**APPROVED direction:**
- Mobile-first web application
- Map is the primary interface
- OpenStreetMap-derived base tiles
- Campus-specific data layer rendered over the base map
- Floating search and map controls
- Bottom-sheet patterns for destination and route panels
- Lightweight — minimize data and battery use

**APPROVED decision (DEC-T01):** Responsive HTML5, CSS, and modular JavaScript with MapLibre GL JS for interactive map rendering.

**CURRENT implementation:** Django-rendered HTML, mobile-first CSS and native ES modules. MapLibre GL JS `6.10.0` is loaded from a pinned CDN URL. Search remains usable when map initialization fails.

The public locator separates browser acquisition (`geolocation.js`), pure validation/stabilization (`location-filter.js`), location UI state (`user-location.js`) and MapLibre rendering (`map.js`). Ordinary public position is transient; only an explicit live-route request sends the currently accepted coordinate to Django, and that request is not persisted.

There is no ordinary-user location-history model, breadcrumb storage or raw-coordinate analytics. Private breadcrumb persistence exists only inside an explicitly started authenticated Path Survey session. Final physical-device survey acceptance remains pending.

---

## Backend

**Status: CURRENT — PHASE 4**

**APPROVED direction:**
- Backend API serving campus data, routing, contributions and editor management

**APPROVED decision (DEC-T02):** Python / Django for business logic, REST APIs, and administrative/editor capabilities.

**CURRENT implementation:** Django `5.2.17` LTS serves the public map, explicit read-only destination/search contracts, manual/live route endpoints, anonymous contributions, authenticated place/entrance/internal-place/path editing, contribution-resolution records and private Path Survey/review workflows.

---

## Database

**Status: CURRENT — LOCAL PHASE 4**

**APPROVED direction:**
- Persistent storage for campus locations, walkable paths, public contributions, editor accounts
- Must support geographic data (coordinates, paths)
- Must clearly separate DEMO data from FIELD VERIFIED data

**APPROVED decision (DEC-T03):** Managed PostgreSQL (Neon preferred; Supabase compatible alternative).

**CURRENT implementation:** SQLite stores local places, categories, aliases, entrances, floors, internal places, contributions/resolutions, routing nodes/segments/anchors, arrival connectors and private survey/verification evidence. Portable Django ORM fields and JSON geometry preserve a PostgreSQL-compatible migration path. No production database infrastructure exists.

---

## Authentication

**Status: CURRENT — AUTHENTICATED EDITOR AND ADMIN PERMISSIONS**

**APPROVED:**
- Normal users require **no account** for navigation, search or contributions
- Editors and administrators require authenticated access

**APPROVED decision (DEC-T06, DEC-T09):** Django's built-in authentication (`django.contrib.auth`) for admin-provisioned editor accounts.

Editors use Django sessions plus explicit model/custom permissions. Administrators retain account, taxonomy and trusted moderation functions. Normal public users still require no account.

---

## Map Tiles

**Status: CURRENT**

**APPROVED:**
- OpenStreetMap-derived tiles as the base geographic context
- OSM coverage does not determine YCT Map quality
- YCT Map maintains its own campus data layer independent of OSM

**APPROVED decision (DEC-T04, DEC-T11):** OpenStreetMap-derived tiles via MapLibre GL JS, initially using OpenFreeMap's official Liberty style. The base-map provider must remain reasonably replaceable.

The style URL and MapLibre module URL are passed to the frontend as explicit configuration rather than coupled to campus records.

Sprint 002 adds a version-controlled orientation-only GeoJSON snapshot derived from OpenStreetMap way `671850885`. It provides a subtle campus fill, outline, label and geometry-derived framing. Its source metadata is retained with the file. It does not verify individual buildings, entrances, paths or destinations.

YCT Map data and OpenStreetMap remain separate systems. Local destination, alias, entrance, internal-location, path, verification and editor changes do not write back to OSM. Any future OSM contribution requires a separate deliberate editing workflow (DEC-T15).

---

## Routing

**Status: CURRENT — PHASE 4 PRE-CLOSEOUT**

**APPROVED direction:**
- Routing applies only within YabaTech campus boundaries
- Routes use campus walkable path data maintained by YCT Map
- Path distances calculated from geographic geometry, not manually entered
- GPS noise must not trigger unnecessary rerouting

**APPROVED decision (DEC-T05):** Shortest-path network graph algorithm (Dijkstra / A*) operating over YCT Map's connected walkable path linestring geometry.

**CURRENT implementation:** Active Django network rows become an immutable adjacency graph. A* uses geometry-derived metres plus an admissible Haversine heuristic and reconstructs traversal-oriented geometry. `EntranceNetworkAnchor` connects a physical Entrance to a graph node; an optional editor-approved connector LineString then extends the A* result from that node to the exact entrance coordinate. Distance, ETA, markers and route bounds use the composed geometry. Legacy `LocationNetworkAnchor` rows remain an explicit compatibility fallback.

The primary development graph is imported from a reviewed OSM/Overpass snapshot into YCT Map-owned records with source references and `UNVERIFIED` state. The import is not a live OSM dependency, does not write back, and does not confer field verification.

---

## Storage

**Status: NOT STARTED**

No file storage requirements identified for V1 (no location photographs in V1).

---

## Deployment

**Status: NOT STARTED**

**APPROVED decision (DEC-T07, DEC-T08):** Web application deployed on Render, database hosted on Neon, initial platform subdomain with custom DNS support.

---

## Architecture Diagram

```
[User Browser / Mobile Device]
           |
           v
   [Frontend Web App]  <----[Map Tile Provider]
           |
           v
     [Backend API]
      |         |
      v         v
[Database]   [Auth Service]
```

The browser frontend, public destination and route endpoints, local database, routing services, transient live-location pipeline, controlled rerouting, contribution queue/resolution audit, place/path editor, Path Survey evidence and explicit revision-bound segment verification are implemented. Physical owner field acceptance and production infrastructure remain pending.

## Contribution Moderation Foundation

Sprint 004 adds a separate `contributions` application. Anonymous users submit a bounded report through `POST /api/contributions/`; Django validates controlled enums, active location references, coordinate ranges and required fields before saving a `PENDING` record. A request UUID provides retry idempotency. A three-success session quota is separate from the broader hashed-IP abuse ceiling, so ordinary validation mistakes do not consume accepted-submission capacity.

Django staff administration is the only moderation interface in this sprint. `APPROVED`, `REJECTED` and `MERGED` decisions record the moderator and review time. Approval means accepted input for later editor action; it neither changes `Location` data nor grants `FIELD_VERIFIED` status.

Phase 3 is OWNER ACCEPTED / COMPLETE. Live positions, route progress and rerouting evidence remain transient; contribution records persist only intentionally submitted report data. Physical-phone GPS/navigation/rerouting and all field verification remain outside the accepted boundary.

---

## Known Architectural Principles

- Mobile-first and lightweight
- Map is the primary interface
- No user accounts required for normal use
- Demo data must be structurally separate from verified campus data
- Routing is campus-only
- Real YabaTech facts must never be invented — use demo data or field verification

---

## Known Limitations

- Indoor route geometry is not in V1; Internal Places use outdoor arrival plus textual indoor handoff
- Routing uses paths maintained in YCT Map data — quality depends on field verification
- Current OSM-derived routing paths and anchors are `UNVERIFIED`; service-road access and exact entrances require later review and field survey
- Browser live-location acquisition/display, live-origin progress and controlled rerouting exist; final physical-device survey acceptance remains pending
- Live locations are matched transiently to the routing graph; matched coordinates and progress remain unpersisted
- Building geometry relies on available data; complex irregular polygons may be simplified initially
- Parallel or closely adjacent segment matching is heuristic and requires human review
- Entrance connectors currently begin at existing graph nodes; segment-aware mid-edge attachment remains future work
- Cloudflare Quick Tunnel support is development-only and is not a deployment architecture

---

## Conflicts / Open Questions

No unresolved Sprint 001 architecture decision remains. The exact future spatial/PostGIS representation is deliberately deferred until routing/path requirements require it.

---

## Phase 4 Sprint 001 Editor Foundation

The custom editor is a server-rendered Django interface under `/editor/`. Django session authentication, CSRF middleware and model permissions form the security boundary; hiding a control is never treated as authorization.

`Location` continues as the UUID outdoor-place identity so routing anchors and contribution foreign keys remain stable. The new domain fields are physical place type, multi-category membership, publication lifecycle, representative point and audit actors. Legacy category and entrance-coordinate fields remain intentionally available only for Phase 1–3 compatibility and are not routing entrance replacements.

```
Authenticated Editor
        |
        v
permission-gated Django view -> explicit ModelForm -> Location + aliases/categories
                                                     |
                         Published + complete only --+--> public GeoJSON
                                                     |
                         LocationNetworkAnchor ------+--> routing graph
```

The Editor group is provisioned after migrations with only the required location/alias/category-view permissions. Administrators retain account and taxonomy administration through Django admin. No public registration, entrance model, internal-place model or field-capture system exists in Sprint 001.

## Phase 4 Sprint 003 Mapping Tools

The editor reuses the Sprint 002 MapLibre point-selector controller for representative points and routing nodes. Browser geolocation is a one-shot sample with visible accuracy, rejection above the safe threshold and manual adjustment; saving always assigns `UNVERIFIED`. Combined representative/primary-entrance capture requires explicit confirmation before replacing an existing primary entrance.

Approved contributions enter a separate resolution queue. Multiple resolution actions may reference locations, entrances, nodes or segments; recording an action does not publish, verify or automatically mutate campus data. Routing edits use nullable actor audit fields. Connected nodes cannot be moved directly, segment impact reports remaining endpoint degree and anchor counts, and splitting is an explicit atomic operation that retains the original segment as inactive history.

### Sprint 004 Pre-Build Architecture Risks

Path Survey Mode needs new evidence/session concepts rather than adding breadcrumb fields to `WalkableSegment`. The plan must decide survey-session ownership and lifecycle, accuracy/timestamp retention, privacy/retention limits, pause/resume recovery, outlier and stationary classification, trace-to-segment matching, partial coverage, ambiguous-match review and explicit verification authorization.

Raw survey samples must be immutable evidence input and must never silently rewrite graph geometry. Opening a survey, walking near a segment or obtaining one good sample must not grant `FIELD_VERIFIED`. A reviewed verification action should identify its actor, evidence/session, affected geometry/version and decision time while publication and routing availability remain independent.

### Phase 4 Sprint 004 Implemented Evidence Architecture

Path Survey Mode stores private editor evidence in `PathSurvey` and ordered `PathSurveySample` records rather than adding breadcrumbs to `WalkableSegment`. Explicit Draft/Active/Paused/Completed/Reviewed/Abandoned transitions govern acquisition; reopening an interrupted Active record does not restart browser geolocation. Brief outages use an IndexedDB buffer and idempotent sequence upload.

Completed samples are immutable and never rewrite graph geometry. `SurveySegmentMatch` stores algorithmic classification separately from reviewer disposition and binds evidence to a segment revision/fingerprint. `SegmentVerificationRecord` preserves explicit grant, revoke and geometry-invalidation history with nullable actors. Verification permissions are separate from ordinary editing; publication and routing availability remain independent.

ACTIVE and PAUSED survey pages render a read-only MapLibre evidence view. Existing `WalkableSegment` geometry is reference data, the current browser position is a separate point, and the live blue trace is reconstructed from authenticated server-returned usable samples. The map has no mutation controls, rejected readings never enter the line, and map/style failure is isolated from capture, IndexedDB buffering and synchronization.

## Phase 4 Sprint 002 Destination Architecture

`Entrance` belongs to an outdoor `Location`; `InternalPlace` belongs to that same Location and may select one active same-parent entrance. Otherwise it falls back to the parent's active primary entrance. `EntranceNetworkAnchor` connects the chosen arrival entrance to the existing walkable graph. The staged resolver prefers this path and retains `LocationNetworkAnchor` only as a compatibility fallback for migrated Phase 1–3 data.

An `EntranceNetworkAnchor` may hold a short, editor-approved connector `LineString` beginning at the selected `WalkableNode` and ending exactly at the Entrance point. A* still solves graph-node to graph-node; routing composition appends the destination connector or prepends its reverse for a supported entrance origin. Geometry-derived connector length contributes to route distance and ETA. Existing null-connector anchors retain explicit legacy node-only behavior and are never silently presented as exact entrance arrival.

Internal Places have no indoor geometry. Their destination resolution chooses an explicit active same-parent routing entrance or the parent primary entrance, routes outdoors to that entrance and preserves floor, room/code, wing and `direction_note` as a textual handoff. Live arrival announces the Entrance, not the room.

Published records do not claim routing readiness. Public serializers expose `routing_available` and `routing_unavailable_reason`; the UI disables Directions but preserves search and display. Strict model validation rejects cross-parent floors/entrances and inactive routing entrances. At most one active primary entrance is enforced in the database.

## Public Destination Density and Semantic Zoom

The public map keeps the existing published-location GeoJSON endpoint and lets MapLibre cluster that source in the browser. Overview and mid zoom show compact count clusters. Once unclustered, editor-designated checkpoints receive permanent green landmark markers while ordinary destinations remain label-and-interaction-target only at close zoom. Cluster selection changes only the camera. Individual destination selection still opens the existing details and Directions flow.

Search and category filtering continue to own the visible feature set through the existing `onFilter` callback. Updating the same clustered GeoJSON source causes MapLibre to recompute clusters, so the map never maintains an independent filter state. A separate one-feature selected-destination source keeps the selected marker and halo visible above clusters without mutating the destination collection. Route lines, route endpoints and live-location layers are deliberately raised above all density layers.

## Navigation Orientation and User-Controlled Camera

`device-orientation.js` owns permission-gated, absolute browser orientation and pure heading math. It accepts a trustworthy native compass heading or absolute alpha corrected for screen orientation, smooths it with shortest-arc circular math and never changes GPS coordinates. The public location controller keeps `deviceFacingHeading` separate from stabilized GPS movement heading. A fresh device heading wins; after four seconds without a device reading, movement heading is the fallback, otherwise the marker remains a dot.

YCT Map keeps geographic camera interaction user-controlled during normal live navigation. Device/movement heading rotates the user marker rather than forcing map bearing. The active route ahead is progressively rendered from trusted route progress. Drag, zoom and rotate gestures therefore remain authoritative; Recenter performs one move to the accepted position at a navigation zoom without changing the user's bearing or enabling a tracking lock. MapLibre's standard compass remains available for a deliberate bearing reset. Orientation is neither sent to Django nor stored, and Path Survey heading remains a separate authenticated evidence workflow.

## Campus-First Map Presentation

YCT Map is campus-first, while OpenFreeMap Liberty retains responsibility for rendering the underlying OSM geography. YCT Map adds only its orientation boundary, destinations, selected state, routing and live-navigation layers; it does not recolour, hide, reorder or otherwise restyle Liberty's buildings, land, paths or POIs. This preserves useful base-map context such as mapped campus services and nearby landmarks without converting any OSM feature into a YCT Map record or verification claim.

The current campus polygon remains an OSM-derived, orientation-only snapshot of way `671850885`; it is not field-verified boundary data. A low-opacity green fill, campus label and soft zoom-responsive outline provide orientation without suppressing native Liberty detail or implying surveyed precision. The outline recedes from 1.5 px/55% at overview zoom to 0.6 px/22% at close zoom. The same unchanged geometry supplies a campus-derived approximately 400 m camera constraint, with zoom limited to 15–20.

Default and Home framing are distinct from whole-campus overview framing. The map first asks MapLibre for the normal boundary-fit camera, uses its zoom only as a baseline, then applies a responsive campus-core profile centred on the approved `[3.37424, 6.51857]` value. Desktop clamps to zoom 17.6–18.0 and mobile to 17.0–17.5. Home is a deliberate north-up core action; the separate overview helper retains complete-boundary `fitBounds` behavior.

Destination focus, initial route fitting and explicit Recenter remain independent camera actions. Search selection may focus its destination and initial route display may fit its complete geometry, but live progress and heading updates do not own or repeatedly move the camera.

Outdoor `Location.is_checkpoint` is an editor-owned wayfinding emphasis flag independent from publication, verification, routing readiness and category. Unclustered checkpoints use a permanent YCT-green 8–9 px landmark with a white outline, subtle halo and earlier label. Ordinary destinations have no permanent point marker: they retain a collision-managed close-zoom label and the shared transparent 30 px-diameter interaction layer. All applicable destinations still participate in the same clustered source, and selected destinations remain prominent through the independent selected source regardless of checkpoint state. Route endpoints and live position remain stronger navigation concepts.
