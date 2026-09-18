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

---

## SPRINT 002 — CAMPUS ORIENTATION, UX REFINEMENT & PHASE 1 COMPLETION

```
Sprint ID:      SPRINT-002
Date:           2026-09-17
Phase:          Phase 1 — Foundation & Map Experience
Status:         IMPLEMENTED / TESTED / OWNER REVIEW REQUIRED
```

### Objective

Make the YabaTech campus immediately identifiable while retaining useful surrounding streets, refine a small number of proven Sprint 001 interactions, and prepare Phase 1 for owner acceptance.

### Starting State / Owner Observation

Sprint 001 was owner verified and accepted. During that verification, surrounding streets and road geometry helped identify the wider area and some base-map buildings appeared visually recognizable. Individual building accuracy was not verified. At wider views, the campus itself was not immediately clear. Recognizable-looking base-map geometry therefore remained contextual information and was not promoted to `FIELD_VERIFIED` YCT Map data.

### Approved Scope Implemented

- Reviewed GeoJSON snapshot derived from OpenStreetMap way `671850885`, with source, version, retrieval and orientation-only metadata
- Subtle campus fill and outline that preserve base-map detail
- Project-controlled `YabaTech Campus` label visible at wider zooms
- Geometry-derived initial `fitBounds()` framing with space for surrounding roads
- Accessible 44 px return-to-campus control with reduced-motion-safe camera behavior
- Selected-destination marker halo
- Category selection now reveals its matching result list for direct browsing
- Category and destination-close controls raised to reliable 44 px touch targets
- OSM/YCT Map ownership rule recorded: local application changes never write back automatically to OSM
- Future editor-only Path Survey Mode recorded for Phase 4 tooling and Phase 5 field use; raw GPS never creates `FIELD_VERIFIED` status

### Verification

- Django system check: passed
- Migration drift check: passed; no model change
- Python compilation: passed
- JavaScript syntax checks: passed
- Campus GeoJSON parsing: passed
- Django tests: 13 passed
- Desktop live map: campus outline, label, surrounding streets, controls and DEMO markers visible
- Return-to-campus control: present, accessible and exercised without runtime error
- Category browse: selected category reveals the matching results
- Destination selection: selected-marker halo and destination details visible
- Mobile browser flow at 390 × 844: passed with no horizontal overflow
- Minimum interactive target checks: category, close and campus controls measured 44 px
- Keyboard result focus and visible focus outline: passed
- Reduced-motion preference detection: passed
- Forced MapLibre-module failure: search, result display and textual destination details remained usable
- Forced OpenFreeMap-style failure: search, result display and textual destination details remained usable
- Browser console/runtime errors: none in the successful external-map pass

### Problems Encountered

- The standard PowerShell HTTP client could not resolve the official OSM API host in the restricted environment.
- An older Sprint 001 Django process was initially still serving port 8000, so the first visual probe did not contain Sprint 002 template configuration.
- The preferred in-app browser connection was unavailable, and the sandboxed browser pass blocked external map resources.

### Resolution

- The approved way was retrieved read-only from the official OSM API using the alternate permitted network client; its closed node sequence was converted directly to GeoJSON without estimating coordinates.
- The exact stale local Django process was identified and replaced with the current server.
- Browser verification used an isolated hidden Chrome profile. The failure-mode pass was retained as graceful-degradation evidence, then the successful map path was rerun with approved network access and software WebGL.

### Data Integrity

- The boundary is an OSM-derived orientation reference, not YCT Map field verification.
- All six destinations remain synthetic `DEMO` records.
- No visible building, gate, path or destination was converted to `FIELD_VERIFIED`.
- No OSM write-back, automatic synchronization, routing, distance, ETA, GPS, editor or contribution feature was implemented.

### Evidence Required for Acceptance

- `P1-S2-A-campus-orientation.png`
- `P1-S2-B-phase1-final-ux.png`
- One short Phase 1 recording: open app → orient on campus → search/browse → select destination → inspect destination card

### Ending State

Sprint 002 is implemented and technically verified. Phase 1 remains IN PROGRESS until the owner completes the acceptance flow and explicitly accepts Sprint 002 and Phase 1.

### Commit

Not committed — owner review required.

### Acceptance Addendum — 2026-09-17

This addendum preserves the implementation-time record above and records the later owner decision without rewriting sprint history.

- Phase 1 Sprint 002 was formally OWNER ACCEPTED.
- Phase 1 was formally OWNER ACCEPTED.
- Campus orientation, boundary, surrounding-road context, return-to-campus behavior, search, category discovery, destination selection, responsive details and graceful degradation passed automated and owner verification.
- One LOW-severity cosmetic carryover remains: `YabaTech Campus` text may repeat at close zoom because the label is placed from polygon geometry.
- The carryover does not affect data integrity or field-verification status and is approved for correction as the first Phase 2 Sprint 001 implementation action.
- The fix must retain the trusted boundary, geometry-derived framing, surrounding-road context and return-to-campus control, and must not change real or DEMO location data.
- Approved Phase 1 milestone commit message: `feat: complete Phase 1 campus orientation and UX refinement`.
- Phase 2 Sprint 001 — Walkable Network & Routing Foundation — is the next approved sprint. Implementation still requires the standalone `BUILD` command.

---

## Phase 2 — Sprint 001: Walkable Network & Routing Foundation

**Date:** 2026-09-17
**Status:** IMPLEMENTED — OWNER REVIEW REQUIRED

### Objective and Result

Established a persistent, geometry-based DEMO walkable network and database-to-graph boundary without calculating or presenting routes. The Phase 1 repeated-label carryover was resolved first with one deterministic point label while preserving the campus polygon and viewport framing.

### What Was Built

- Minimal `WalkableNode` and `WalkableSegment` models with controlled verification state, active state, directionality and GeoJSON geometry.
- Geometry validation and dynamic Haversine length over every LineString leg.
- Immutable in-memory adjacency graph with reverse arcs for bidirectional segments.
- Diagnostics for malformed geometry, zero length, self-edges and duplicate/reverse-duplicate segments.
- Replaceable fixture with 5 explicitly labelled DEMO nodes and 5 DEMO segments.
- DEBUG-only GeoJSON inspection endpoint and dashed DEMO overlay with a hide/show control and “no route calculated” notice.

### Verification and Boundary

Django system check passed and all 23 automated tests passed, including the 13 Phase 1 regressions. No A*/Dijkstra selection, calculated route, ETA, GPS, real path, field verification or editor feature was built. `BUILD_JOURNAL.md` remains unchanged until acceptance.

Required owner evidence: `P2-S1-A-demo-walkable-network.png`, `P2-S1-B-routing-foundation.png`, and replacement `P1-S2-B-phase1-final-ux-fixed.png`.

**Commit:** Not committed — owner review required.

### Acceptance Addendum — 2026-09-17

This addendum preserves the implementation-time record above and records the later owner decision without rewriting sprint history.

- Phase 2 Sprint 001 was formally OWNER ACCEPTED.
- The owner verified the DEBUG-only DEMO network, node rendering, inspection toggle, explicit “no route calculated” state, corrected single campus label, and preserved Phase 1 discovery flow.
- A separate regression review found no Phase 2 change to the accepted OpenFreeMap configuration or Phase 1 camera behavior.
- The purple network and DEMO destinations remain synthetic and geographically unverified. Observed mismatches with real walkways or destination positions are demonstration-data limitations, not evidence of a routing-engine defect.
- Real pathways and destination positions remain subject to later population and field verification.
- Approved milestone commit message: `feat: establish walkable network and routing foundation`.
- Phase 2 Sprint 002 — A* Route Calculation and Route Results — is next. No Sprint 002 implementation is included in this milestone.

---

## Phase 2 — Sprint 002: A* Route Calculation, Distance & Baseline ETA

**Date:** 2026-09-18
**Status:** IMPLEMENTED — OWNER REVIEW REQUIRED

### Objective and Result

Implemented an independent A* routing service over the accepted Sprint 001 graph foundation. Results contain ordered nodes and segments, traversal-oriented LineString geometry, geometry-derived total distance and approximate baseline ETA.

### What Was Built

- Pure A* with Haversine heuristic, predecessor reconstruction and deterministic stable-ID tie behavior.
- Immutable route result plus invalid-node, missing-anchor and no-route errors.
- Correct forward/reverse geometry assembly, junction deduplication and intermediate-vertex retention.
- Approximate ETA based on the approved `1.35 m/s` fallback.
- Routing-owned `LocationNetworkAnchor` model, migration and five DEMO anchors.
- Node-to-node service independent of `Location`, plus a location-anchor adapter.
- Narrow DEBUG endpoints and inspector for DEMO route selection, highlighting, distance and ETA.

### Verification and Boundary

All 45 automated tests pass, including the 23 prior tests. No GPS, live speed, progress, rerouting, turn instructions, final navigation sheet, real campus data, editor tooling or field verification was implemented. The route remains a calculation over synthetic DEMO topology, not verified campus guidance.

Required owner evidence: `P2-S2-A-calculated-demo-route.png` and `P2-S2-B-route-distance-eta.png`.

**Commit:** Not committed — owner review required.

### Acceptance Addendum — 2026-09-18

This addendum preserves the implementation-time record above and records the later owner decision without rewriting sprint history.

- Phase 2 Sprint 002 was formally OWNER ACCEPTED.
- The owner verified DEMO endpoint selection, successful A* calculation, distinct selected-route rendering, distance, approximate ETA, multiple inspection states and continued Phase 1/Sprint 001 behavior.
- Current route and path geometry remains synthetic and geographically unverified; observed geographic inaccuracies are fixture limitations rather than routing-engine defects.
- Sprint 003 must add a clear static start marker and red destination indicator. Static origin presentation must not imitate live GPS. A directional live-position triangle/chevron and heading remain conditional on reliable future live data.
- Existing OSM/OpenFreeMap-visible paths may inform future graph construction, but rendered paths never become routing edges automatically. Explicit YCT Map geometry, editor review and separate field verification remain required.
- Future editor validation should flag ordinary outdoor path/building-footprint intersections while supporting deliberate reviewed passage/corridor exceptions.
- Approved milestone commit message: `feat: add A* route calculation distance and baseline ETA`.
- Phase 2 Sprint 003 is next. No Sprint 003 implementation is included in this milestone.
