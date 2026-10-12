# Current State — YCT Map

> This document must be kept short and updated after every substantial sprint.
> The full build roadmap lives in `docs/project/operations/BUILD_PIPELINE.md`.

---

## Snapshot

| Field | Value |
|-------|-------|
| **Date** | 2026-10-12 |
| **Branch** | `main` |
| **Current Phase** | PHASE 4 — POST-CLOSEOUT LOCATION RELIABILITY CORRECTION |
| **Pipeline Phase** | LIVE-LOCATION RELIABILITY HARDENING — IMPLEMENTED LOCALLY / OWNER RETEST REQUIRED |
| **Latest Meaningful State** | Fresh multi-sample public location acquisition, hard-reset reacquisition, explicit navigation readiness and transient GPS recovery; local asset token `location-reliability-1` |

---

## Project Status

| Area | Status |
|------|--------|
| Application implementation | FINAL SYSTEM CLOSEOUT SWEEP COMPLETE; LIVE-LOCATION RELIABILITY CORRECTION IMPLEMENTED LOCALLY |
| Product definition | COMPLETE FOR V1 |
| Documentation / governance | CURRENT THROUGH LOCAL LIVE-LOCATION RELIABILITY CORRECTION |
| Build pipeline | COMPLETE THROUGH PHASE 4 CLOSEOUT |
| Tech stack & architecture decisions | RESOLVED (DEC-T01–DEC-T22 accepted; no schema migration 0011) |
| Campus production dataset | INITIAL OWNER-CONFIRMED DATA: New Building, Sports Complex, Food Tech New Building |
| Field verification | LOCAL BASELINE AUDITED AND VERIFIED VIA COMMAND; PRODUCTION PROMOTION COMMANDS STAGED FOR OWNER |
| Routing dataset | 49 active nodes (1..49) and 54 active segments (A..BB); 3 active entrance anchors |
| Deployment | EXISTING RENDER + NEON SERVICE UNCHANGED; THIS LOCAL CORRECTION IS NOT COMMITTED, PUSHED OR DEPLOYED |
| Test suite | 255 DJANGO + 153 JAVASCRIPT TESTS PASSING; SYSTEM, MIGRATION, SYNTAX AND WHITESPACE GATES CLEAN |

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

The public live-location reliability correction is **IMPLEMENTED LOCALLY / OWNER RETEST REQUIRED** on top of commit `bda6992`. Cold starts and reacquisition now request uncached browser fixes (`maximumAge: 0`) and reject epoch-based callbacks older than five seconds. The public marker is not published, focused or made route-eligible until at least three reasonable fixes converge across at least three seconds. The 20-second acquisition deadline now changes the guidance state only: it never promotes one callback, and the watcher continues trying.

Manual refresh, stale-position expiry and foreground return after at least 30 seconds clear the displayed point plus all previous-session filter evidence before reacquiring. A lone callback can therefore no longer borrow history from a previous location session. Retryable timeout/unavailable events keep acquisition alive, or retain an existing confirmed estimate with its original evidence timestamp, rather than causing terminal error churn. Live route setup now additionally requires the explicit `navigationReady` signal; accurate-looking but unconfirmed positions cannot become route origins. The marker remains unsnapped, coordinates remain transient, the routing graph and backend matching rules are unchanged, and the production service/database have not been touched. Local browser assets use `location-reliability-1` so an eventual deployment cannot reuse the previous mobile bundle.

The off-network live-start correction is IMPLEMENTED LOCALLY / OWNER REVIEW REQUIRED on top of commit `a3e059b`. Real-device evidence showed that a precise Sports Complex position can still be about 65 m from the nearest mapped segment, beyond the unchanged 40 m safety threshold. When that specific safe-match failure occurs near another route-capable campus place, the public client now offers the existing mapped route from that place's configured entrance and holds progress/rerouting until the user reaches the entrance. It explicitly states that no route from the live dot to the entrance is claimed. No graph geometry, backend matching threshold, destination data, migration or verification state is changed.

The local graph audit found 49 active nodes and 54 active segments in strongly connected components of 41, 6, 1 and 1 nodes. All three local route-capable destinations and entrance anchors are in the 41-node component; every ordered destination pair routes successfully and all active segment models validate. The final closeout normalized all active node labels to positive sequential integers (1..49) and all active segment labels to uppercase bijective base-26 sequences (A..BB). All source references and provenance remain intact in source_reference and source_type.

The baseline verification management command (`verify_current_map_baseline`) transitions active, published Locations, active Entrances of published places, active WalkableNodes, active WalkableSegments, and active EntranceNetworkAnchors to `FIELD_VERIFIED` with reason "Owner-approved final map baseline", creating append-only `SegmentVerificationRecord` rows. The command is fully idempotent.

Public route verification (`public_route` and `public_route_from_position`) now returns `FIELD_VERIFIED` when all traversed graph elements are `FIELD_VERIFIED`. The destination panel and navigation HUD hide all unverified notices and badges for `FIELD_VERIFIED` destinations and routes. Attribution is updated to "YCT Map campus data · OSM-derived route data".

Lower-right HUD collision between MapLibre controls (NavigationControl zoom buttons and compass arrow needle) and Locate Me is resolved via coordinated CSS variables (`--locate-me-clearance` and `--map-ctrl-bottom-offset`), guaranteeing touch clearance without vertical overlap. Desktop baseline uses `--locate-me-height: 5.75rem` to clear the desktop card and error states completely, maintaining a 26px clear gap to the compass arrow button. Mobile portrait and landscape maintain dedicated compact clearances and offsets. All cache busting tokens across backend constants, templates, and JS imports are synchronized to `system-closeout-2`.

Graph visualization on the walkable path editor overview (`/editor/paths/`) and the map developer network inspector now features real-time, zoom-dependent visual labels (`minzoom: 16.5`): nodes dynamically expand and display their bold centered numerical ID (e.g. `24`), while segments display their uppercase letter designation (e.g. `AB`) directly along the path line with a crisp white halo, preserving clean uncluttered campus-wide overview while providing instant clarity upon zooming in.

---

## Known Blockers

Physical Samsung/Edge retesting is required for cold start, return after more than 30 seconds in the background, temporary GPS timeout/unavailable recovery, stationary use and an actual walking route. Browser geolocation remains limited by phone hardware, radio visibility, OS settings and the browser; this correction prevents stale or weak evidence from being presented as confirmed accuracy but cannot create native/Google-grade sensor fusion.

---

## Next Approved Task

Owner verification of the local corrected build on a live mobile device. Commit, push and deployment require separate owner authorization after that review.

---

## Deployment Status

The existing production deployment remains on the last pushed baseline. This dirty local build uses cache token `location-reliability-1`; it has not been committed, pushed or deployed. No Neon, Render, migration, graph or verification-state operation was performed.
