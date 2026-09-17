# Sprint Log — YCT Map

This is an append-only record of project sprints.

Add a new entry after every substantial sprint. Do not edit past entries.

---

## SPRINT 000 — PROJECT BASELINE

```
Sprint ID:      SPRINT-000
Date:           2026-09-16
Type:           Foundation / Documentation
```

### Objective

Establish a durable project operating system and documentation structure for YCT Map so future agents and developers can recover project context from the repository without depending on conversation history.

### Starting State

- Empty repository
- 8 governance files at root level (no structure)
- No application code
- No git history
- No product documentation

### Work Performed

- Created root files: README.md, AGENTS.md, CLAUDE.md, GEMINI.md
- Organized governance files into `docs/project/governance/`
- Updated DEFINITION_OF_DONE.md with SOFTWARE VERIFIED vs FIELD VERIFIED distinction
- Updated STOP_CONDITIONS.md with YCT Map campus data integrity rule (#17)
- Updated PROJECT_RESUME_PROMPT.md with correct `docs/project/` paths
- Created product documents: PROJECT_BRIEF, V1_SCOPE, UX_FLOW, EDITOR_WORKFLOW, ROADMAP, DESIGN_SYSTEM
- Created technical intent documents: ARCHITECTURE, DATA_MODEL, ROUTING, SECURITY, ENVIRONMENT, DEPLOYMENT, TEST_STRATEGY, CODE_STYLE, API_CONTRACT
- Created operations documents: CURRENT_STATE, BUILD_PIPELINE, DECISIONS, SPRINT_LOG, KNOWN_ISSUES, RISKS, BACKLOG, RELEASE_CHECKLIST, CHANGELOG
- Created docs/project/README.md (documentation index)
- Removed obsolete root-level governance duplicates

### Files / Systems Affected

All documentation. No application code written.

### Tests

No tests — documentation-only sprint.

### Decisions Recorded

- DEC-001 through DEC-008 recorded in DECISIONS.md (from owner product specification)
- DEC-T01 through DEC-T10 identified as open (owner confirmation required)

### Problems

None.

### Deferred Work

All application implementation. All technology stack decisions (DEC-T01 through DEC-T10).

### Ending State

Documentation system established. Repository ready for owner review.

### Next Recommended Sprint

Owner reviews documentation and resolves open technology decisions (DEC-T01 through DEC-T10), then Sprint 001 — Core Infrastructure.

### Commit

Not committed — awaiting owner authorization.

---

<!-- Add SPRINT-001 below after owner review and first implementation sprint -->

## SPRINT 001 — CORE FOUNDATION AND INITIAL MAP EXPERIENCE

```
Sprint ID:      SPRINT-001
Date:           2026-09-17
Phase:          Phase 1 — Foundation & Map Experience
Status:         IMPLEMENTED / TESTED / OWNER REVIEW REQUIRED
```

### Objective

Create the first runnable YCT Map experience: an interactive YabaTech-area map with explicitly synthetic DEMO destinations, search, selection and responsive destination details.

### Approved Scope Implemented

- Django 5.2 LTS project and public map application
- Local SQLite development configuration compatible with the approved PostgreSQL direction
- Minimal `Location` and `LocationAlias` models with controlled choices
- Initial migration and explicitly loaded synthetic DEMO fixture
- Small public GeoJSON endpoint with name, partial, alias and category search
- MapLibre GL JS 6.10.0 with OpenFreeMap Liberty
- OSM-derived initial viewport `[3.37424, 6.51857]`
- Mobile-first floating search, categories, markers and destination bottom sheet
- Desktop destination card and responsive map controls
- Loading, no-result, data-error and map-error behavior
- Reduced-motion handling and keyboard-accessible native controls

### Verification

- Django system check: passed
- Migration drift check: passed
- Python compilation: passed
- JavaScript syntax checks: passed
- Django tests: 12 passed
- Live HTTP check: passed at `http://127.0.0.1:8000/`
- Desktop browser flow: passed
- Mobile browser flow at 390 × 844: passed
- Partial alias search and destination selection: passed
- Horizontal-overflow check: passed
- Browser console/runtime errors: none in final pass

### Problems Encountered

The available sandbox Python distribution lacked `venv` and ignored `PYTHONPATH`. Dependencies were isolated in a Git-ignored workspace package directory for verification. Standard developer setup remains a normal virtual environment as documented in the root README.

### Deferred / Explicitly Excluded

Routing, distance, ETA, GPS, rerouting, contributions, moderation, editor CRUD, real campus population, field verification, indoor maps and detailed 3D.

### Ending State

Sprint 001 is implemented and software-tested with synthetic DEMO data. Owner acceptance and milestone screenshots remain required before the sprint or Phase 1 is marked complete.

### Commit

Not committed — owner review required.

### Acceptance Addendum — 2026-09-17

This addendum preserves the original implementation-time record above and records the later owner decision without rewriting that history.

- Owner manually verified and accepted Sprint 001.
- The Sprint 001 application foundation, tests, documentation updates and student-facing `BUILD_JOURNAL.md` were approved for a dedicated milestone commit.
- Approved milestone commit message: `feat: complete Phase 1 Sprint 001 map foundation`.
- All six demonstration destinations remain explicitly synthetic and use the `DEMO` verification state.
- Sprint acceptance does not convert demonstration, recognizable-looking base-map, contribution or unverified data into `FIELD_VERIFIED` campus information.
- Sprint 002 is the next approved discussion/planning task. Its implementation requires a separate standalone `BUILD` command.
