# Current State — YCT Map

> This document must be kept short and updated after every substantial sprint.
> The full build roadmap lives in `docs/project/operations/BUILD_PIPELINE.md`.

---

## Snapshot

| Field | Value |
|-------|-------|
| **Date** | 2026-09-17 |
| **Branch** | `main` |
| **Current Phase** | PHASE 1 — FOUNDATION & MAP EXPERIENCE |
| **Pipeline Phase** | Sprint 001 OWNER VERIFIED / ACCEPTED; Sprint 002 approved for discussion/planning |
| **Latest Meaningful Commit** | Sprint 001 milestone (`feat: complete Phase 1 Sprint 001 map foundation`) |

---

## Project Status

| Area | Status |
|------|--------|
| Application implementation | SPRINT 001 OWNER VERIFIED / ACCEPTED |
| Product definition | SUBSTANTIALLY COMPLETE |
| Documentation / governance | SUBSTANTIALLY COMPLETE |
| Build pipeline | SUBSTANTIALLY COMPLETE |
| Tech stack & architecture decisions | RESOLVED (DEC-T01–DEC-T14 accepted) |
| Campus production dataset | NOT YET POPULATED |
| Demo dataset | 6 SYNTHETIC DEMO LOCATIONS — local fixture |
| Field verification | NOT STARTED |
| Deployment | NOT STARTED |
| Test suite | 12 TESTS PASSING |

---

## Pipeline Position

See `docs/project/operations/BUILD_PIPELINE.md` for the full 5-phase plan.

```
Phase 1 — Foundation & Map Experience          IN PROGRESS
Phase 2 — Routing & Navigation                 NOT STARTED
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

---

## Active Work

Sprint 001 is owner verified and accepted. Its dedicated milestone commit contains the accepted application foundation, documentation and student-facing build journal.

---

## Known Blockers

No implementation blocker. Sprint 002 implementation still requires the standalone `BUILD` command under the Build Control Protocol.

---

## Next Approved Task

Phase 1 Sprint 002 — Campus Orientation, UX Refinement & Phase 1 Completion. Discussion/planning is approved; do not begin implementation until the standalone `BUILD` command.

---

## Deployment Status

NOT STARTED. No deployment exists.
