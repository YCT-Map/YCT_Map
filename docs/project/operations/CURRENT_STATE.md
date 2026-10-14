# Current State — YCT Map

> This document must be kept short and updated after every substantial sprint.
> The full build roadmap lives in `docs/project/operations/BUILD_PIPELINE.md`.

---

## Snapshot

| Field | Value |
|-------|-------|
| **Date** | 2026-10-14 |
| **Branch** | `main` |
| **Current Phase** | PHASE 4 — POST-CLOSEOUT LIVE-ROUTING STABILITY CORRECTION |
| **Pipeline Phase** | DESTINATION-AWARE LIVE ROUTING — IMPLEMENTED LOCALLY / OWNER RETEST REQUIRED |
| **Latest Meaningful State** | Destination-aware graph matching, explicit approach/arrival states, visible route-setup recovery and an owner-attested local `FIELD_VERIFIED` baseline; asset token `live-routing-stability-1` |

---

## Project Status

| Area | Status |
|------|--------|
| Application implementation | FINAL SYSTEM CLOSEOUT SWEEP COMPLETE; LIVE-ROUTING STABILITY CORRECTION IMPLEMENTED LOCALLY |
| Product definition | COMPLETE FOR V1 |
| Documentation / governance | CURRENT THROUGH LOCAL LIVE-ROUTING STABILITY CORRECTION |
| Build pipeline | COMPLETE THROUGH PHASE 4 CLOSEOUT |
| Tech stack & architecture decisions | RESOLVED (DEC-T01–DEC-T22 accepted; no schema migration 0011) |
| Campus production dataset | INITIAL OWNER-CONFIRMED DATA: New Building, Sports Complex, Food Tech New Building |
| Field verification | CURRENT ELIGIBLE LOCAL BASELINE OWNER-ATTESTED AND PROMOTED TO `FIELD_VERIFIED`; FUTURE, EDITED AND DEMO RECORDS RETAIN NORMAL VERIFICATION RULES |
| Routing dataset | 49 active nodes (1..49) and 54 active segments (A..BB); 3 active entrance anchors |
| Deployment | EXISTING RENDER + NEON SERVICE UNCHANGED; THIS LOCAL CORRECTION IS NOT COMMITTED, PUSHED OR DEPLOYED |
| Test suite | 264 DJANGO + 162 JAVASCRIPT TESTS PASS; SYSTEM CHECK, MIGRATION DRIFT, SYNTAX AND WHITESPACE GATES CLEAN |

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

The live-routing stability correction is **IMPLEMENTED LOCALLY / OWNER RETEST REQUIRED** on top of commit `bbec57d`. Route setup now validates the confirmed transient position, limits candidate graph segments to those that can reach the selected destination, and returns an explicit state: `ON_NETWORK`, `APPROACH_REQUIRED`, or `ARRIVAL_CANDIDATE`. Ordinary safe matching remains narrow. The wider sparse-campus allowance is available only within the approved campus boundary and never changes the graph.

When `APPROACH_REQUIRED` is returned, the UI draws a separate dashed orientation guide from the live position to the matched graph point. It is explicitly not represented as a mapped walkway, is excluded from route distance and ETA, and holds normal progress/rerouting until the mapped route corridor is joined. A destination-arrival proximity reading is only an `ARRIVAL_CANDIDATE`; the client requires repeated evidence over time before displaying Arrived. Route setup failures, malformed responses and render failures now restore a usable form with a visible actionable error instead of leaving the mobile panel stuck or silent. The Directions action remains visible with a specific disabled reason when a destination cannot route.

Fresh multi-sample acquisition and hard-reset reacquisition from the preceding reliability correction remain intact. Live coordinates remain transient, the public marker remains unsnapped, no location history is created, and the routing graph geometry is unchanged. Browser assets use `live-routing-stability-1` so a later deployment cannot reuse the preceding mobile bundle.

The local graph audit found 49 active nodes and 54 active segments in strongly connected components of 41, 6, 1 and 1 nodes. All three local route-capable destinations and entrance anchors are in the 41-node component; every ordered destination pair routes successfully and all active segment models validate. The final closeout normalized all active node labels to positive sequential integers (1..49) and all active segment labels to uppercase bijective base-26 sequences (A..BB). All source references and provenance remain intact in source_reference and source_type.

The baseline verification management command (`verify_current_map_baseline`) now transitions only eligible `UNVERIFIED` records in the owner-attested current baseline: published Locations and InternalPlaces, active Entrances under published places, active WalkableNodes and WalkableSegments, and eligible Location/Entrance network anchors. Eligibility is locked to the pre-2026-10-14 data snapshot, so rerunning the command cannot silently verify records created or edited afterward. It never promotes `DEMO`, draft, archived or inactive records, remains idempotent, and creates append-only segment audit records. The current eligible local baseline has been reconciled to `FIELD_VERIFIED`; new records and materially edited records continue to use the normal verification defaults and demotion rules.

Public route verification (`public_route` and `public_route_from_position`) now returns `FIELD_VERIFIED` when all traversed graph elements are `FIELD_VERIFIED`. The destination panel and navigation HUD hide all unverified notices and badges for `FIELD_VERIFIED` destinations and routes. Attribution is updated to "YCT Map campus data · OSM-derived route data".

Lower-right HUD collision between MapLibre controls (NavigationControl zoom buttons and compass arrow needle) and Locate Me remains resolved via coordinated CSS variables (`--locate-me-clearance` and `--map-ctrl-bottom-offset`). All current cache-busting tokens across backend constants, templates and JavaScript imports are synchronized to `live-routing-stability-1`.

Graph visualization on the walkable path editor overview (`/editor/paths/`) and the map developer network inspector now features real-time, zoom-dependent visual labels (`minzoom: 16.5`): nodes dynamically expand and display their bold centered numerical ID (e.g. `24`), while segments display their uppercase letter designation (e.g. `AB`) directly along the path line with a crisp white halo, preserving clean uncluttered campus-wide overview while providing instant clarity upon zooming in.

---

## Known Blockers

Physical Samsung/Edge retesting is required for cold start, return after more than 30 seconds in the background, temporary GPS timeout/unavailable recovery, stationary use, sparse-campus approach guidance, route-corridor joining and confirmed arrival. Browser geolocation remains limited by phone hardware, radio visibility, OS settings and the browser; these corrections improve safe interpretation and recovery but cannot create native/Google-grade sensor fusion.

---

## Next Approved Task

Owner verification of the local corrected build on a live mobile device. Commit, push and deployment require separate owner authorization after that review.

---

## Deployment Status

The existing production deployment remains on the last pushed baseline. This dirty local build uses cache token `live-routing-stability-1`; it has not been committed, pushed or deployed. No Neon or Render operation was performed. Verification reconciliation was applied only to the ignored local SQLite database; production data and routing geometry are unchanged.
