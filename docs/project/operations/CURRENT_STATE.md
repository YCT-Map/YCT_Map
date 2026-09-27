# Current State — YCT Map

> This document must be kept short and updated after every substantial sprint.
> The full build roadmap lives in `docs/project/operations/BUILD_PIPELINE.md`.

---

## Snapshot

| Field | Value |
|-------|-------|
| **Date** | 2026-09-27 |
| **Branch** | `main` |
| **Current Phase** | PHASE 4 — EDITOR & MAPPING TOOLS |
| **Pipeline Phase** | PHASE 4 SPRINT 004 IMPLEMENTATION + TECHNICAL AUDIT COMPLETE / PHYSICAL OWNER ACCEPTANCE PENDING |
| **Latest Meaningful Commit** | Phase 4 specification baseline (`docs: establish Phase 4 campus data and editor specification`) |

---

## Project Status

| Area | Status |
|------|--------|
| Application implementation | PHASE 4 SPRINTS 001–003 OWNER ACCEPTED; SPRINT 004 PHYSICAL OWNER ACCEPTANCE PENDING |
| Product definition | SUBSTANTIALLY COMPLETE |
| Documentation / governance | SUBSTANTIALLY COMPLETE |
| Build pipeline | SUBSTANTIALLY COMPLETE |
| Tech stack & architecture decisions | RESOLVED THROUGH PHASE 2 (DEC-T01–DEC-T18 accepted) |
| Campus production dataset | INITIAL OWNER-CONFIRMED DATA: New Building and Sports Complex; all retained records remain UNVERIFIED |
| Demo/development dataset | Live working DEMO Locations removed; DEMO fixtures retained only for automated tests |
| Field verification | NOT STARTED |
| Routing dataset | 47 OSM-derived nodes plus 2 manual nodes; 54 OSM-derived segments; 2 active entrance anchors; all UNVERIFIED |
| Deployment | PRODUCTION CONFIGURATION PREPARED; NO DEPLOYMENT PERFORMED |
| Test suite | 176 DJANGO + 77 JAVASCRIPT TESTS PASSING |

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

Phase 4 Sprints 001, 002 and 003 are OWNER ACCEPTED / COMPLETE. Sprint 002 now includes multiple entrances, floors and internal places, explicit entrance anchoring, editor-approved arrival-connector geometry, exact physical-entrance route completion and textual indoor handoff without claiming indoor routing.

Phase 4 Sprint 004 is IMPLEMENTATION COMPLETE / TECHNICAL AUDIT COMPLETE / PHYSICAL OWNER ACCEPTANCE PENDING. It adds explicit mobile Path Survey sessions, private accuracy-classified samples with temporary IndexedDB buffering, revision-bound trace matching, separate reviewer disposition, append-only verification history and permission-gated grant/revoke actions. No survey automatically edits the graph or grants `FIELD_VERIFIED`.

---

## Known Blockers

Physical Samsung/mobile Path Survey acceptance still requires final real-device and real-campus review over an approved HTTPS origin. No segment has been field verified by this software build; the existing OSM-derived graph remains `UNVERIFIED`. Parallel/closely adjacent path matching remains heuristic, browser geolocation cannot guarantee room-level positioning, segment-aware entrance attachment remains future work, and detailed contribution-resolution owner QA remains intentionally deferred.

---

## Next Approved Task

Complete the remaining physical-device and real-campus acceptance for Phase 4 Sprint 004. Phase 4 remains open until that evidence is accepted. Detailed ContributionResolution QA is deferred but is not represented as completed.

---

## Deployment Status

NOT STARTED. No production deployment exists. Cloudflare Quick Tunnel support is development-only.
