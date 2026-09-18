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

---

## Phase 2 — Sprint 003: User-Facing Navigation UX & Phase 2 Completion

**Date:** 2026-09-18
**Status:** IMPLEMENTED — OWNER REVIEW REQUIRED

### Objective and Result

Converted the accepted routing engine into a mobile-first user flow: select an anchored destination, choose a non-live DEMO origin, calculate a route, see distinct static endpoints, inspect distance/ETA, and clear or change the route without refreshing.

### What Was Built

- Explicit public route endpoint with no graph IDs or DEBUG terminology.
- `routing_available` location contract field and conditional Directions entry point.
- Origin-selection, calculating, route, inline error, change and clear states.
- Blue cased route, blue static `S` marker and larger red `D` marker.
- Route geometry bounds with route-panel-aware mobile/desktop padding.
- Compact responsive route sheet with start/follow/arrive guidance and DEMO warning.
- Complete purple network hidden by default; DEBUG tools retained separately in a collapsed developer panel.

### Verification and Boundary

All 48 automated tests pass, including every earlier routing and Phase 1 regression. No browser GPS, moving marker, heading, personal-speed estimation, route progress, rerouting, real path import, editor collision logic or field verification was implemented.

Required acceptance evidence: `P2-S3-A-navigation-route-endpoints.png`, `P2-S3-B-mobile-navigation-summary.png`, and `P2-R-navigation-flow.mp4`.

`BUILD_JOURNAL.md` Sprint 003 and the Phase 2 summary remain pending until owner acceptance.

**Commit:** Not committed — owner review required.

### Owner Review Correction Addendum — 2026-09-18

This addendum preserves the initial implementation record above. The first owner review did not accept Sprint 003 because the screenshots exposed the existing DEBUG route inspector rather than making the separate normal-user Directions flow evident.

- Investigation confirmed that active anchored DEMO destinations returned `routing_available: true` and that the public route endpoint and user-navigation implementation existed.
- Unversioned browser modules could combine current HTML/CSS with stale JavaScript, leaving Directions hidden and making the DEBUG inspector appear to be the only route entry point.
- A shared UI asset version now refreshes the stylesheet, application entry module and all imported application modules together.
- Directions availability is explicitly derived from the boolean routing contract, and origin selection handles the absence of another anchored DEMO location safely.
- Fresh mobile-browser verification completed the normal flow without opening Developer tools and rendered a blue cased route, a blue static `S` at the route start, a red `D` at the route end, distance, approximate ETA, guidance and change/clear controls.
- All 49 automated tests pass. Sprint 003 remains unaccepted pending owner re-verification.

### Second Owner Review Correction Addendum — 2026-09-18

The second owner review also did not accept Sprint 003. Although cache-safe assets exposed Directions, the owner still did not receive an unmistakable normal-user route transition. Investigation found no Directions-to-DEBUG code path and reproduced the public flow in a clean Edge session, but confirmed that panel ownership was non-atomic: `app.js` closed the destination panel before an optional navigation-controller call could confirm that choosing-origin state opened.

- `app.js` now owns the explicit `browsing`, `destination-selected`, `choosing-origin` and `route-available` interface states.
- User navigation is initialized before destination interaction is registered, and the destination card closes only after `begin()` succeeds.
- Origin selection starts with an explicit placeholder, excludes the selected destination and enables Show route only after a valid origin is chosen.
- Cancel returns to the selected destination card; Clear returns to browsing; Change destination returns focus to discovery.
- A repository-owned Node behaviour suite executes Directions intent, choosing-origin population, public route request/result rendering, cancel and clear behavior.
- All 49 Django tests and 3 JavaScript behaviour tests pass. A fresh Microsoft Edge mobile run reached `route-available` with Developer tools closed and rendered the blue public route plus endpoint-aligned blue `S` and red `D` markers.
- Sprint 003 remains unaccepted pending owner re-verification. No Phase 3 work is included.

### OSM Walkable Network Realism Pass — 2026-09-18

After confirming that the public Sprint 003 navigation flow worked, the owner rejected the five-segment synthetic geometry as too unrealistic for continued product review. The routing engine was retained unchanged while its primary local dataset was replaced.

- Captured a reproducible Overpass snapshot inside OSM campus way `671850885` at OSM base timestamp `2026-09-18T06:32:00Z`.
- Reviewed 30 candidate ways: 29 service ways and one explicit footway.
- Added controlled OSM/manual/synthetic provenance to routing nodes and segments.
- Added a deterministic, transactional dry-run/apply importer with access/construction rejection, campus-boundary filtering and topology splitting at shared/arrival nodes.
- Loaded 47 OSM-derived `UNVERIFIED` nodes, 54 `UNVERIFIED` segments and six reviewed `UNVERIFIED` destination anchors.
- Added the missing Medical Centre anchor. Every pair among the six DEMO destinations now produces a route.
- Preserved the original synthetic topology only as an automated-test fixture.
- Added ODbL/source documentation and explicit UI wording that the route geometry is OSM-derived, unverified and not field-verified guidance.
- All 52 Django tests and 3 JavaScript behaviour tests pass. Sprint 003 and Phase 2 remain unaccepted pending owner visual review; no Phase 3 work is included.

### Final Acceptance Addendum — 2026-09-18

This addendum preserves the implementation and correction history above and records the final owner decision.

- Phase 2 Sprint 003 was formally OWNER ACCEPTED.
- Phase 2 — Routing & Navigation was formally OWNER ACCEPTED.
- The owner verified the public Directions flow, static route endpoints, Medical Centre routing and the materially more plausible OSM-derived development network.
- The accepted development dataset contains 47 OSM-derived `UNVERIFIED` nodes, 54 `UNVERIFIED` segments and six destination anchors. No imported record is `FIELD_VERIFIED`.
- The original five-segment synthetic graph remains only for deterministic automated tests and algorithm edge cases.
- A* was already correct against the synthetic graph. Poor visible realism came from poor input geometry; replacing the graph data improved routes without changing A*, reconstruction, distance or ETA logic.
- The missing Medical Centre Directions action was caused by an absent active `LocationNetworkAnchor`; a deliberate non-field-verified anchor resolved it.
- Accepted evidence is `P2-S3-A-navigation-route-endpoints.png`, `P2-S3-B-medical-centre-route.png`, supporting `P2-S3-C-osm-unverified-network.png`, and phase recording `P2-R-navigation-flow.mp4`.
- Browser GPS, live progress, rerouting, Path Survey Mode, complete editor mapping, verified entrances and field-verified paths remain deferred.
- Phase 3 is next for discussion/planning only. No Phase 3 implementation is included.

---

## Phase 3 — Sprint 001: Live Location Foundation

**Date:** 2026-09-18
**Status:** IMPLEMENTED — OWNER REVIEW REQUIRED

### Objective and Result

Established a user-triggered, privacy-preserving browser geolocation pipeline that distinguishes raw samples from accepted display positions and represents location quality honestly. The sprint intentionally stops before live-origin routing, route progress and rerouting.

### What Was Built

- Explicit unsupported, idle, requesting, locating, active, low-accuracy, denied, unavailable, timed-out and stopped states.
- `getCurrentPosition()` followed by a cleaned-up `watchPosition()` session with visibility pause/resume.
- Pure coordinate, timestamp, accuracy, heading and apparent-jump validation.
- Accuracy bands at 25 m, 60 m and a 100 m display ceiling.
- A blue live dot when heading is unavailable and a chevron only when device heading and meaningful speed are present.
- A restrained GeoJSON accuracy halo whose geographic radius follows the reported metre accuracy.
- First-reliable-position focus, later marker-only updates and an explicit recenter control.
- Stop behavior that clears the watcher and live map presentation.
- No storage, backend request, migration, coordinate logging or route integration.

### Verification and Boundary

All 52 Django tests and 8 JavaScript tests pass. New behavior coverage exercises invalid samples, poor accuracy, stale readings, implausible jumps, heading reliability, unsupported geolocation, watcher cleanup and permission revocation, permission denial, accepted positions, recenter and stop. Existing manual routing remains the only route-origin mechanism.

Localhost and simulated-browser review may verify UI behavior. Physical-phone GPS must be reported separately and remains unverified until an approved HTTPS origin exists. Required owner evidence should use simulated campus coordinates: `P3-S1-A-live-location-marker.png` and `P3-S1-B-location-permission-fallback.png`.

`BUILD_JOURNAL.md` remains unchanged until owner acceptance. No commit has been created.

### Acceptance Addendum — 2026-09-18

This addendum records the owner decision without rewriting the implementation-time record.

- Phase 3 Sprint 001 was formally OWNER ACCEPTED.
- Verification status is `SIMULATED GEOLOCATION VERIFIED`; physical-phone GPS is not verified.
- The owner verified Locate me, permission prompting, a simulated campus position, the blue live marker, metre-based halo, low-accuracy presentation, recenter, stop, denial fallback and preserved manual Directions.
- A previously accepted position at approximately 40 m accuracy correctly remained displayed when a substantially worse approximately 100 m sample arrived.
- Minor non-blocking carryover: explain in the UI when the previous better location is being retained after a worse sample is rejected.
- Ordinary-user coordinates are not persisted, stored as history/breadcrumbs, added to analytics or sent to the backend. Evidence uses simulated campus coordinates.
- Accepted evidence: `P3-S1-A-live-location-marker.png` and `P3-S1-B-location-permission-fallback.png`.
- Phase 3 Sprint 002 is next for discussion/planning only. No Sprint 002 implementation is included.

## Phase 3 — Sprint 002: Live Route Start, Route Progress & Dynamic ETA

**Status:** IMPLEMENTED — OWNER REVIEW REQUIRED
**Date:** 2026-09-18

### Implementation Record

- Added a CSRF-protected POST route endpoint accepting an ephemeral accepted position and destination UUID.
- Added complete-segment projection, quality-aware 25/40 m matching thresholds and request-local virtual graph origins that respect one-way traversal.
- Kept the measured live marker distinct from the network-matched route start; no false connector is drawn and no live coordinates are persisted or echoed as separate response fields.
- Added live position as an optional route origin while preserving every manual origin flow.
- Added route-line projection, stable progress, remaining distance, filtered walking-speed estimates, explicit 1.35 m/s fallback ETA, stationary/uncertain states and two-sample arrival confirmation.
- Added explicit UI copy when a worse position is rejected and the previous better position is retained.
- Added server and browser-module coverage; 60 Django and 12 JavaScript tests pass.
- Physical-phone GPS is not verified. Owner review must use an approved HTTPS origin for that claim; localhost simulated traces remain `SIMULATED GEOLOCATION` evidence only.
- `BUILD_JOURNAL.md` remains unchanged until owner acceptance. Sprint 003 rerouting has not started.

### Acceptance Addendum — 2026-09-18

- Phase 3 Sprint 002 was formally OWNER ACCEPTED with the verification label `SIMULATED LIVE NAVIGATION VERIFIED`.
- The owner visually verified the live-origin option, a safe network match, route initialization, separation of the measured marker and matched origin, fixed-route behavior, advancing progress, decreasing remaining distance and personal walking-pace ETA behavior.
- The owner also verified that a simulated point approximately 69 m from the nearest eligible segment fails safely with HTTP 422.
- The representative accepted route targeted `DEMO — Hostel`, began at approximately 209 m and later showed approximately 185 m and 179 m remaining with simulated 3 m accuracy.
- Deterministic automated tests—not owner observation—verify stationary-state handling, stationary pace isolation, ETA hierarchy, arrival confirmation, progress stability, snap rejection and live/manual regressions.
- Physical-phone GPS/navigation is not verified. The active OSM-derived routing graph remains `UNVERIFIED` and is not field-verified guidance.
- Primary evidence is `P3-S2-A-live-origin-route.png` and `P3-S2-B-dynamic-eta-progress.png`; the rejected-snap image is supporting evidence.
- Phase 3 Sprint 003 is next for discussion/planning only. No Sprint 003 implementation is included.

## Phase 3 — Sprint 003: Off-Route Detection & Controlled Rerouting

**Status:** IMPLEMENTED — OWNER REVIEW REQUIRED
**Date:** 2026-09-18

### Implementation Record

- Added a deterministic client-side off-route state machine separating location quality, active-route distance and confirmed deviation.
- Added a bounded accuracy-aware corridor. Accuracy worse than 25 m produces uncertainty and cannot count as off-route evidence.
- Added three-sample/eight-second confirmation with credible-movement requirements; one anomaly, recovery, backtracking and arrival do not reroute.
- Reused the Sprint 002 CSRF-protected live-origin endpoint only after confirmed deviation; Django remains authoritative for safe graph matching and A*.
- Added one-request locking, ten-second new-route stabilization, a 30-second cooldown and a 20 m post-reroute movement gate.
- Successful reroutes retain destination and personal pace, replace route geometry without hijacking the camera, and reset route-specific progress/stationary/arrival state.
- Failed reroutes retain a faded previous route, present restrained failure copy and expose a retry action.
- Added deterministic active-graph-derived deviation and poor-accuracy traces for automated and owner verification.
- All 60 Django tests and 23 JavaScript tests pass before owner review.
- `BUILD_JOURNAL.md` remains unchanged until owner acceptance. Physical-device rerouting is not verified and no commit has been created.

### Acceptance Addendum — 2026-09-18

- Phase 3 Sprint 003 was formally OWNER ACCEPTED with the label `SIMULATED REROUTING VERIFIED`.
- The owner visually verified the checking state, controlled reroute, route replacement, unchanged `DEMO — Hostel` destination, continued live-position updates, decreasing post-reroute distance and camera preservation.
- Observed remaining distance after replacement included approximately 39 m, 31 m and 25 m.
- Deterministic automated tests—not owner observation—verify the exact three-sample/eight-second rule, single-anomaly recovery, poor-GPS uncertainty, valid backtracking, request locking, stabilization, cooldown, movement gate, failure handling, pace preservation and arrival precedence.
- Physical-device rerouting is not verified. OSM-derived graph geometry remains `UNVERIFIED`; no field verification has occurred.
- Primary evidence is `P3-S3-A-off-route-detected.png` and `P3-S3-B-rerouted-navigation.png`, both using simulated coordinates.
- Phase 3 Sprint 004 is next for discussion/planning only. No Sprint 004 implementation is included.

## Phase 3 Sprint 004 — Implementation Complete / Owner Review Required (2026-09-18)

Objective: complete the Phase 3 contribution foundation and mobile/accessibility polish without expanding into Phase 4 editor tooling.

Implemented:
- Added a minimal persisted `Contribution` model with controlled type/status choices, optional existing-location target, proposed place/category/point, moderation outcome fields and UUID replay protection.
- Added `POST /api/contributions/` with CSRF, server validation, bounded input, active-target validation, coordinate validation, session plus hashed-IP throttling and honeypot handling.
- Added a mobile-first anonymous contribution panel with existing-place and missing-place modes, deliberate map-point selection, loading/success/error states, retained retry data and no collection of contact details or location history.
- Added staff-only Django-admin review. Moderation decisions record reviewer/time but do not modify `Location`, publish a contribution or grant `FIELD_VERIFIED` status.
- Preserved active route state while the contribution panel temporarily owns the foreground and added narrow/landscape overflow and touch-target refinements.

Verification: 70 Django tests and 27 JavaScript tests pass; JavaScript syntax, Django checks and migration drift are clean. Owner visual verification and evidence remain required. `BUILD_JOURNAL.md` is intentionally unchanged until acceptance.

Next: owner verifies the Sprint 004 flows and captures `P3-S4-A-anonymous-contribution.png` and `P3-S4-B-mobile-navigation-polish.png`. Do not begin Phase 4 before explicit Phase 3 acceptance.

### Acceptance Addendum — 2026-09-18

- Phase 3 Sprint 004 and Phase 3 were formally OWNER ACCEPTED / COMPLETE.
- The owner verified anonymous corrections and missing-place reports, deliberate map-point submission, pending moderation, approval, rejection with a moderator note, reviewer audit fields, unchanged public map data after moderation, manual-routing regression and the approximately 360×800 mobile route layout.
- Owner testing exposed high-precision MapLibre coordinates failing six-decimal model validation and repeated failures consuming the normal quota. Client/server normalization, coordinate-specific feedback and separate accepted/abuse counters corrected the defect before acceptance.
- Final verification is 74 Django tests and 34 JavaScript tests, with syntax, Django checks, migration drift and whitespace checks clean.
- Primary evidence: `P3-S4-A-anonymous-contribution.png` and `P3-S4-B-mobile-navigation-polish.png`. Supporting admin evidence records pending, approved and rejected states.
- Approval records an accepted report for later authenticated editor action; it does not mutate live map data or grant `FIELD_VERIFIED` status.
- Physical-phone GPS/navigation/rerouting, OSM-derived graph geometry and all campus data remain unverified in the field.
- Phase 4 implementation has not started.
