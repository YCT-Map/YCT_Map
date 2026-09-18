# Current State — YCT Map

> This document must be kept short and updated after every substantial sprint.
> The full build roadmap lives in `docs/project/operations/BUILD_PIPELINE.md`.

---

## Snapshot

| Field | Value |
|-------|-------|
| **Date** | 2026-09-18 |
| **Branch** | `main` |
| **Current Phase** | PHASE 2 — ROUTING & NAVIGATION |
| **Pipeline Phase** | Phase 2 Sprint 002 OWNER ACCEPTED; Sprint 003 is next |
| **Latest Meaningful Commit** | Phase 2 Sprint 002 milestone (`feat: add A* route calculation distance and baseline ETA`) |

---

## Project Status

| Area | Status |
|------|--------|
| Application implementation | PHASE 2 SPRINT 002 OWNER ACCEPTED |
| Product definition | SUBSTANTIALLY COMPLETE |
| Documentation / governance | SUBSTANTIALLY COMPLETE |
| Build pipeline | SUBSTANTIALLY COMPLETE |
| Tech stack & architecture decisions | RESOLVED THROUGH PHASE 2 SPRINT 002 (DEC-T01–DEC-T17 accepted) |
| Campus production dataset | NOT YET POPULATED |
| Demo dataset | 6 DEMO locations; 5 DEMO nodes, 5 DEMO segments and 5 DEMO anchors |
| Field verification | NOT STARTED |
| Deployment | NOT STARTED |
| Test suite | 45 TESTS PASSING |

---

## Pipeline Position

See `docs/project/operations/BUILD_PIPELINE.md` for the full 5-phase plan.

```
Phase 1 — Foundation & Map Experience          ACCEPTED
Phase 2 — Routing & Navigation                 IN PROGRESS
Phase 3 — Live Navigation & Core Product       NOT STARTED
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

---

## Active Work

Phase 2 Sprint 002 is owner accepted. Phase 2 remains IN PROGRESS pending the user-facing route experience in Sprint 003.

---

## Known Blockers

No implementation blocker. The repeated campus-label issue is resolved by a deterministic point label.

---

## Next Approved Task

Phase 2 Sprint 003 — user-facing route experience and clearer origin/destination visualization. Do not implement until separately authorized under the Build Control Protocol.

---

## Deployment Status

NOT STARTED. No deployment exists.
