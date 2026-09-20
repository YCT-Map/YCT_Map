# Current State — YCT Map

> This document must be kept short and updated after every substantial sprint.
> The full build roadmap lives in `docs/project/operations/BUILD_PIPELINE.md`.

---

## Snapshot

| Field | Value |
|-------|-------|
| **Date** | 2026-09-18 |
| **Branch** | `main` |
| **Current Phase** | PHASE 3 — LIVE NAVIGATION & CORE PRODUCT SYSTEMS |
| **Pipeline Phase** | PHASE 3 OWNER ACCEPTED / COMPLETE |
| **Latest Meaningful Commit** | Phase 3 Sprint 004 milestone (`feat: complete Phase 3 live navigation and contributions`) |

---

## Project Status

| Area | Status |
|------|--------|
| Application implementation | PHASE 3 OWNER ACCEPTED / COMPLETE |
| Product definition | SUBSTANTIALLY COMPLETE |
| Documentation / governance | SUBSTANTIALLY COMPLETE |
| Build pipeline | SUBSTANTIALLY COMPLETE |
| Tech stack & architecture decisions | RESOLVED THROUGH PHASE 2 (DEC-T01–DEC-T18 accepted) |
| Campus production dataset | NOT YET POPULATED |
| Demo/development dataset | 6 DEMO locations; 47 OSM-derived UNVERIFIED nodes, 54 segments and 6 UNVERIFIED anchors |
| Field verification | NOT STARTED |
| Deployment | NOT STARTED |
| Test suite | 74 DJANGO + 34 JAVASCRIPT TESTS PASSING |

---

## Pipeline Position

See `docs/project/operations/BUILD_PIPELINE.md` for the full 5-phase plan.

```
Phase 1 — Foundation & Map Experience          ACCEPTED
Phase 2 — Routing & Navigation                 ACCEPTED
Phase 3 — Live Navigation & Core Product       ACCEPTED
Phase 4 — Editor & Mapping Tools               NOT STARTED
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

Phase 3 Sprint 004 and Phase 3 are OWNER ACCEPTED / COMPLETE. The owner-approved Phase 4 campus-data/editor specification is integrated at `docs/project/phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md`. Phase 4 implementation has not started.

---

## Known Blockers

Physical-phone GPS/navigation/rerouting remains unverified because no owner-approved HTTPS test origin exists. The OSM-derived graph remains `UNVERIFIED`, and full outside-campus product behavior is deferred.

---

## Next Approved Task

Phase 4 sprint discussion/planning against the approved specification. Implementation still requires an approved sprint plan and standalone `BUILD` command.

---

## Deployment Status

NOT STARTED. No deployment exists.
