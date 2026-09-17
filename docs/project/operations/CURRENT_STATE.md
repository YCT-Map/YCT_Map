# Current State — YCT Map

> This document must be kept short and updated after every substantial sprint.
> The full build roadmap lives in `docs/project/operations/BUILD_PIPELINE.md`.

---

## Snapshot

| Field | Value |
|-------|-------|
| **Date** | 2026-09-17 |
| **Branch** | `main` |
| **Current Phase** | PHASE 2 — ROUTING & NAVIGATION (planning) |
| **Pipeline Phase** | Phase 1 OWNER ACCEPTED; Phase 2 Sprint 001 awaiting standalone `BUILD` |
| **Latest Meaningful Commit** | Phase 1 milestone (`feat: complete Phase 1 campus orientation and UX refinement`) |

---

## Project Status

| Area | Status |
|------|--------|
| Application implementation | PHASE 1 OWNER ACCEPTED; PHASE 2 NOT STARTED |
| Product definition | SUBSTANTIALLY COMPLETE |
| Documentation / governance | SUBSTANTIALLY COMPLETE |
| Build pipeline | SUBSTANTIALLY COMPLETE |
| Tech stack & architecture decisions | RESOLVED THROUGH PHASE 1 (DEC-T01–DEC-T15 accepted) |
| Campus production dataset | NOT YET POPULATED |
| Demo dataset | 6 SYNTHETIC DEMO LOCATIONS — local fixture |
| Field verification | NOT STARTED |
| Deployment | NOT STARTED |
| Test suite | 13 TESTS PASSING |

---

## Pipeline Position

See `docs/project/operations/BUILD_PIPELINE.md` for the full 5-phase plan.

```
Phase 1 — Foundation & Map Experience          ACCEPTED
Phase 2 — Routing & Navigation                 READY FOR BUILD AUTHORIZATION
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

---

## Active Work

Phase 1 is owner accepted. Phase 2 Sprint 001 — Walkable Network & Routing Foundation — is approved as the next task, but implementation has not started.

---

## Known Blockers

No implementation blocker. The repeated `YabaTech Campus` label at close zoom is a LOW-severity cosmetic carryover approved for correction as the first Phase 2 Sprint 001 implementation action.

---

## Next Approved Task

Phase 2 Sprint 001 — Walkable Network & Routing Foundation. Begin implementation only after the standalone `BUILD` command.

---

## Deployment Status

NOT STARTED. No deployment exists.
