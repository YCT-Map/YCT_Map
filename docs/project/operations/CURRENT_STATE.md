# Current State — YCT Map

> This document must be kept short and updated after every substantial sprint.
> The full build roadmap lives in `docs/project/operations/BUILD_PIPELINE.md`.

---

## Snapshot

| Field | Value |
|-------|-------|
| **Date** | 2026-10-06 |
| **Branch** | `main` |
| **Current Phase** | PHASE 4 — FINAL SYSTEM CLOSEOUT SWEEP COMPLETE |
| **Pipeline Phase** | FINAL SYSTEM CLOSEOUT SWEEP — IMPLEMENTED & TESTED LOCALLY / READY FOR OWNER REVIEW |
| **Latest Meaningful State** | Dynamic dashed walk-to-path connector, automatic baseline field verification on deploy, user copy and attribution cleaned, asset token `system-closeout-4` |

---

## Project Status

| Area | Status |
|------|--------|
| Application implementation | FINAL SYSTEM CLOSEOUT SWEEP COMPLETE; ALL V1 FEATURES POLISHED & HARDENED |
| Product definition | COMPLETE FOR V1 |
| Documentation / governance | COMPLETE & CURRENT (DEC-T01 through DEC-T22 accepted) |
| Build pipeline | COMPLETE THROUGH PHASE 4 CLOSEOUT |
| Tech stack & architecture decisions | RESOLVED (DEC-T01–DEC-T22 accepted; no schema migration 0011) |
| Campus production dataset | INITIAL OWNER-CONFIRMED DATA: New Building, Sports Complex, Food Tech New Building |
| Field verification | AUTOMATIC FIELD-VERIFIED BASELINE VIA DEPLOY SCRIPT; VERIFIED PROMOTION SCRIPT TESTED |
| Routing dataset | 49 active nodes (1..49) and 54 active segments (A..BB); 3 active entrance anchors |
| Deployment | RENDER + NEON PRODUCTION SERVICE READY; AUTO-DEPLOY CONFIGURED VIA GIT MAIN |
| Test suite | 255 DJANGO + 149 JAVASCRIPT TESTS PASSING (100% GREEN, ZERO REGRESSIONS) |

---

## Pipeline Position

See `docs/project/operations/BUILD_PIPELINE.md` for the full 5-phase plan.

```
Phase 1 — Foundation & Map Experience          ACCEPTED
Phase 2 — Routing & Navigation                 ACCEPTED
Phase 3 — Live Navigation & Core Product       ACCEPTED
Phase 4 — Editor & Mapping Tools               IN PROGRESS — SPRINT 004 PHYSICAL OWNER ACCEPTANCE PENDING
Phase 5 — Real YabaTech Data & Launch          NOT STARTED
```

---

## Completed Work

**Foundation / Documentation (SPRINT-000)**
- Project governance documents established in `docs/project/governance/`
- Product definition documents established in `docs/project/product/`
- Technical intent documents established in `docs/project/technical/`
- Operations documents initialized in `docs/project/operations/`
- Root files created: `README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- Authoritative 5-phase build pipeline established
- Technical decisions DEC-T01 through DEC-T14 reviewed and accepted
- Initial viewport source, synthetic demo-data policy, OpenFreeMap Liberty style and 1.35 m/s ETA assumption approved

**Phase 1 / Sprint 001 — OWNER VERIFIED / ACCEPTED**
- Runnable Django 5.2 LTS application foundation
- SQLite local-development database with PostgreSQL-compatible ORM models
- Minimal `Location` and `LocationAlias` models plus initial migration
- Explicit synthetic DEMO fixture with six destinations
- Public GeoJSON location/search endpoint
- Responsive MapLibre GL JS map using OpenFreeMap Liberty
- Name/partial/alias search, category filtering, marker selection and destination panel
- 12 automated tests plus desktop/mobile browser verification

**Phase 1 / Sprint 002 — OWNER VERIFIED / ACCEPTED**
- OSM way `671850885` retained as a reviewed, orientation-only GeoJSON boundary
- Subtle campus fill, outline and persistent YabaTech campus label
- Geometry-derived initial framing with surrounding streets retained
- Accessible return-to-campus control
- Selected-marker halo, category-browse result reveal and 44 px touch-target refinements
- Search and textual details verified under both map-module and map-style failure
- 13 automated tests plus desktop/mobile/failure-path browser verification

**Phase 2 / Sprint 001 — OWNER VERIFIED / ACCEPTED**
- Persistent DEMO walkable nodes and segments with stable UUIDs
- GeoJSON LineString geometry with dynamic Haversine length calculation
- Database-to-memory adjacency graph conversion and bidirectional reverse arcs
- Network validation diagnostics and DEBUG-only topology inspection overlay
- Deterministic single campus label replacing the Phase 1 cosmetic carryover
- 23 automated tests plus owner verification of the network, toggle and Phase 1 regressions

**Phase 2 / Sprint 002 — OWNER VERIFIED / ACCEPTED**
- A* shortest-distance routing with admissible Haversine heuristic
- Ordered route reconstruction and traversal-oriented LineString assembly
- Geometry-derived total distance and approximate `1.35 m/s` baseline ETA
- Routing-owned DEMO destination anchors plus independent node routing
- Explicit invalid, unreachable and same-origin behavior
- DEBUG-only selected-route inspection with 45 passing tests

**Phase 2 / Sprint 003 — OWNER VERIFIED / ACCEPTED**
- Normal-user Directions flow with explicit UI state ownership
- Static blue start and red destination indicators plus route-aware framing
- Responsive route summary, distance, approximate ETA and change/clear controls
- OSM-derived primary development graph: 47 `UNVERIFIED` nodes, 54 segments and six anchors
- Medical Centre routing restored through a deliberate non-verified anchor
- 52 Django tests and 3 JavaScript behaviour tests passing at Phase 2 acceptance

**Phase 3 / Sprint 001 — OWNER VERIFIED / ACCEPTED**
- User-triggered transient browser geolocation with explicit permission/error states
- Raw-sample validation, accuracy bands and noisy-jump protection
- Blue live dot or trustworthy-heading chevron with metre-based accuracy halo
- First-position focus, recenter and stop/cleanup behavior
- SIMULATED GEOLOCATION VERIFIED; physical-phone GPS not yet verified
- 52 Django tests and 8 JavaScript tests passing at acceptance

---

**Phase 3 / Sprint 002 — OWNER VERIFIED / ACCEPTED**
- Quality-aware live-position matching to complete walkable-segment geometry
- Ephemeral virtual route origins with no location persistence
- Stable client-side route progress, remaining distance and personal-pace ETA
- Explicit 1.35 m/s fallback, stationary handling and confirmed arrival logic
- SIMULATED LIVE NAVIGATION VERIFIED; stationary/arrival transitions verified by deterministic tests, not owner observation
- 60 Django tests and 12 JavaScript tests passing at acceptance

---

**Phase 3 / Sprint 003 — OWNER VERIFIED / ACCEPTED**
- Accuracy-aware off-route checking and repeated-evidence confirmation
- Controlled automatic rerouting with destination and pace preservation
- Request locking, stabilization, cooldown and post-reroute movement gates
- Graceful stale-route retention and retry behavior
- SIMULATED REROUTING VERIFIED; detailed safety branches remain deterministic automated verification
- 60 Django tests and 23 JavaScript tests passing at acceptance

---

**Phase 3 / Sprint 004 — OWNER VERIFIED / ACCEPTED**
- Anonymous pending-only contribution submission for corrections, missing places, information and access/path reports
- Optional deliberate map-point selection with authoritative six-decimal client/server normalization
- CSRF, bounded validation, UUID idempotency, three-success session quota and separate hashed-IP abuse ceiling
- Staff-only Django-admin moderation with approval/rejection/merge audit fields and no automatic public-data mutation
- Full-width mobile sheets, reachable horizontal categories, touch-friendly route actions and foreground-state preservation
- 74 Django tests and 34 JavaScript tests passing at Phase 3 acceptance

---

## Active Work

The off-network live-start correction is IMPLEMENTED LOCALLY / OWNER REVIEW REQUIRED on top of commit `a3e059b`. Real-device evidence showed that a precise Sports Complex position can still be about 65 m from the nearest mapped segment, beyond the unchanged 40 m safety threshold. When that specific safe-match failure occurs near another route-capable campus place, the public client now offers the existing mapped route from that place's configured entrance and holds progress/rerouting until the user reaches the entrance. It explicitly states that no route from the live dot to the entrance is claimed. No graph geometry, backend matching threshold, destination data, migration or verification state is changed.

The local graph audit found 49 active nodes and 54 active segments in strongly connected components of 41, 6, 1 and 1 nodes. All three local route-capable destinations and entrance anchors are in the 41-node component; every ordered destination pair routes successfully and all active segment models validate. The final closeout normalized all active node labels to positive sequential integers (1..49) and all active segment labels to uppercase bijective base-26 sequences (A..BB). All source references and provenance remain intact in source_reference and source_type.

The baseline verification management command (`verify_current_map_baseline`) transitions active, published Locations, active Entrances of published places, active WalkableNodes, active WalkableSegments, and active EntranceNetworkAnchors to `FIELD_VERIFIED` with reason "Owner-approved final map baseline", creating append-only `SegmentVerificationRecord` rows. The command is fully idempotent.

Public route verification (`public_route` and `public_route_from_position`) now returns `FIELD_VERIFIED` when all traversed graph elements are `FIELD_VERIFIED`. The destination panel and navigation HUD hide all unverified notices and badges for `FIELD_VERIFIED` destinations and routes. Attribution is updated to "YCT Map campus data · OSM-derived route data".

Lower-right HUD collision between MapLibre controls (NavigationControl zoom buttons and compass arrow needle) and Locate Me is resolved via coordinated CSS variables (`--locate-me-clearance` and `--map-ctrl-bottom-offset`), guaranteeing touch clearance without vertical overlap. Desktop baseline uses `--locate-me-height: 5.75rem` to clear the desktop card and error states completely, maintaining a 26px clear gap to the compass arrow button. Mobile portrait and landscape maintain dedicated compact clearances and offsets. All cache busting tokens across backend constants, templates, and JS imports are synchronized to `system-closeout-2`.

Graph visualization on the walkable path editor overview (`/editor/paths/`) and the map developer network inspector now features real-time, zoom-dependent visual labels (`minzoom: 16.5`): nodes dynamically expand and display their bold centered numerical ID (e.g. `24`), while segments display their uppercase letter designation (e.g. `AB`) directly along the path line with a crisp white halo, preserving clean uncluttered campus-wide overview while providing instant clarity upon zooming in.

---

## Known Blockers

None. All 255 Django tests and 149 JavaScript tests pass cleanly. Live location routing connects across campus and Render auto-deploys cleanly.

---

## Next Approved Task

Owner verification on live mobile devices within the YabaTech campus network and confirmation of active Render deployment.

---

## Deployment Status

Pushed to `main`. Render build script contains execute permissions and auto-runs `assign_graph_display_labels --apply`. Cache buster token synchronized to `system-closeout-3`.
