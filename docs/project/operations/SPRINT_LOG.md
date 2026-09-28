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
---

## Phase 4 — Sprint 001: Editor Access & Campus-Place Foundation

**Status:** IMPLEMENTED — OWNER REVIEW REQUIRED
**Date:** 2026-09-20

### Objective

Establish trusted editor access and evolve the existing UUID `Location` model into an extensible outdoor-place foundation without disrupting accepted public map, routing or contribution behavior.

### Implementation Record

- Evolved `Location` in place with controlled physical place types, multi-category membership, Draft/Published/Archived lifecycle, nullable representative points and nullable creator/updater actors.
- Retained legacy `category`, `entrance_latitude` and `entrance_longitude` as explicitly deprecated compatibility fields; no historical migration or UUID was rewritten.
- Added twelve controlled functional Category records through a data migration and backfilled existing DEMO records, representative coordinates and lifecycle state.
- Added typed aliases with per-place case-insensitive duplicate prevention while allowing aliases to collide across different places.
- Added a least-privilege Editor group, Django session login, POST/CSRF logout and server-side permission enforcement.
- Added a custom responsive editor dashboard, place list, metadata/alias form and archive/reactivate actions. Draft creation requires no raw coordinate input and remains non-public.
- Preserved `LocationNetworkAnchor`, route destination resolution, contribution foreign keys, historical contribution categories and moderation semantics.
- No entrances, entrance-aware routing, internal places, field capture, real campus population or Sprint 002 functionality was introduced.
- Full verification currently passes with 94 Django tests and 34 JavaScript tests. Owner visual review is still required.
- `BUILD_JOURNAL.md` remains unchanged until owner acceptance.

### Local Owner-Test Correction — Survey Counters and Timing

- Corrected the survey UI to distinguish persisted raw, usable (`ACCEPTED` + `WEAK`) and rejected samples. Rejected readings remain private raw evidence and remain excluded from matching.
- Added prospective active-capture accumulation driven only by the explicitly running GPS watcher, with pause/resume/interruption safety and periodic monotonic persistence.
- Kept wall-clock session duration separately labelled. Surveys completed before this correction retain calculable wall-clock duration but explicitly state that historical active-only time was not measured.
- Added migration `routing.0008` for the accumulated active seconds and whether prospective timing was started.
- Correction verification passes with 132 Django and 48 JavaScript tests. No matching, verification, privacy or graph-mutation semantics changed.
- ACTIVE and PAUSED surveys now include a mobile field map with the existing graph, current GPS point and a synchronized usable-evidence trace. Rejected samples never enter the trace, pause preserves it, and MapLibre/basemap failure does not interrupt capture or synchronization. Verification now passes with 133 Django and 49 JavaScript tests.

### Evidence Required After Acceptance

- `P4-S1-A-editor-place-form.png`
- `P4-S1-B-editor-place-list.png`

### Next Step

Owner review and explicit Sprint 001 acceptance. Do not begin Sprint 002 automatically.

### Acceptance Addendum — 2026-09-20

- Phase 4 Sprint 001 was formally OWNER ACCEPTED / COMPLETE; Phase 4 remains IN PROGRESS.
- The owner verified signed-out login redirection, authorized authentication, the custom Places interface, six preserved DEMO records, a synthetic metadata-only Draft, physical type, multiple categories, typed aliases/codes, Draft and UNVERIFIED state, public search exclusion and existing DEMO search/navigation/manual routing.
- Archive/reactivate, login failure, inactive-user behavior, safe redirects, POST logout, permission boundaries, direct-request authorization, taxonomy restrictions, alias collisions, migration preservation, publication validation, CSRF and the full Phase 1–3 regression suite remain automated-test verification rather than owner-manual claims.
- Accepted evidence: `P4-S1-A-editor-place-form.png` and `P4-S1-B-editor-place-list.png`, with supporting login, public-search exclusion and route-regression evidence.
- Final verification is 94 Django tests and 34 JavaScript tests with syntax, compilation, system checks, migration drift and whitespace checks clean.
- No entrances, floors, internal places, entrance-aware routing, field capture, contribution resolution, real campus population or field verification exists yet.
- Sprint 002 is ready for discussion only and requires its own approved plan and standalone `BUILD` command.

---

## Phase 4 — Sprint 002: Entrances, Floors, Internal Places & Entrance-Aware Destinations

**Status:** IMPLEMENTED — OWNER REVIEW REQUIRED
**Date:** 2026-09-20

- Added persisted Entrance, Floor, InternalPlace, InternalPlaceAlias and EntranceNetworkAnchor models without removing legacy compatibility fields.
- Migrated existing anchored DEMO destinations to primary entrances while preserving destination UUIDs, graph nodes and route outcomes.
- Added namespaced internal destination identity, entrance-aware resolution, unified internal search and lazy floor-grouped building directories.
- Added editor entrance map selection, floor/internal-place entry, repeated same-floor entry and routing-readiness warnings.
- Revised the approved plan so publication, verification and routing availability remain independent. Published incomplete destinations remain visible with Directions disabled and an explicit reason.
- Strict validation rejects cross-parent floors/entrances, inactive selected entrances and inactive anchors; the database permits at most one active primary entrance.
- Verification currently passes at 100 Django and 34 JavaScript tests. Owner visual review and evidence remain required. `BUILD_JOURNAL.md` remains unchanged until acceptance.

### Owner-Test Correction — Entrance Selector and Floor Editing

- Owner browser review found that the entrance map selector never initialized because the entry module requested a nonexistent default export from MapLibre's ES module bundle.
- Replaced that import with the proven dynamic named-module pattern, added a reusable selector controller, visible loading/error/selected states, responsive sizing, saved-point initialization, marker replacement and adjacent hidden-coordinate validation feedback.
- Owner review also reached a stale `--noreload` URL configuration that did not contain the newly implemented `floor-edit` pattern. The nested route/view remains permission-protected and parent-scoped; the corrected build was restarted so the route is active.
- Added floor creation/detail/edit/cross-parent/duplicate-level integration tests, nested-route rendering coverage and entrance selector DOM/server/JavaScript behavior tests.
- Final correction verification passes at 107 Django and 36 JavaScript tests. Sprint 002 remains unaccepted and uncommitted pending renewed browser QA.

---

## Phase 4 — Sprint 003: Field Capture, Contribution Resolution & Path Editing

**Status:** IMPLEMENTED — OWNER REVIEW REQUIRED
**Date:** 2026-09-24

- Reused the Sprint 002 point-selector for representative-place and routing-node map capture; one-shot browser samples show accuracy, reject unsafe samples, allow manual adjustment and always save as `UNVERIFIED`.
- Added an explicit confirmation barrier before combined capture can replace an active primary entrance.
- Added a permission-gated approved-contribution queue and repeatable `ContributionResolution` audit actions. Approval/resolution do not publish, mutate records automatically or grant `FIELD_VERIFIED`.
- Added permission-gated node and LineString segment editing, nullable audit actors, connected-node coordinate locking and concrete endpoint-degree/anchor impact warnings.
- Added explicit transactional segment splitting that creates two UNVERIFIED replacements and retains the original as inactive history.
- Corrected category-checkbox layout by excluding checkboxes from full-width input styling and placing each box immediately before its label.
- Final automated verification passes with 113 Django tests and 39 JavaScript tests; system checks, Python/JavaScript syntax, migration drift and whitespace validation are clean.
- Sprint 002 acceptance remains intentionally deferred. No browser automation harness, real campus population, automatic OSM synchronization or commit is included.

### Owner-Test Correction Pass

- Corrected representative-map initialization to use the same working MapLibre ES-module pattern as the entrance selector; current-location controls now initialize independently so map-load failure cannot make the button inert.
- Added visible permission/request, success/accuracy, retry, denied, unavailable and timeout states; samples above 100 m are rejected and successful points remain adjustable and `UNVERIFIED`.
- Moved editor segment geometry onto the actual model-backed JSON form field so Django validates the same LineString drawn by the browser. Two-point and intermediate-vertex geometry now saves and reopens correctly.
- Prevented invalid publication attempts from passing a mutated, unsaved status into destination resolution. Missing representative points remain normal form errors; published unanchored places remain public with Directions unavailable.
- Added a lightweight MapLibre overview of active nodes/segments with manual/OSM provenance distinction, while retaining the editable textual lists.
- Added explicit Places-to-dashboard navigation and preserved combined-capture confirmation plus later independence of Location and Entrance points.
- Correction verification passes with 116 Django and 44 JavaScript tests. No migration, browser harness, commit or push was created.

### Final Acceptance and Stability Sweep — 2026-09-24

- The owner accepted Sprint 003 for closure after verifying checkbox layout, entrance placement/editing, representative-map loading/manual placement/persistence, responsive current-location capture, correct rejection of an approximately 212 m sample, floor editing and internal-place creation. Detailed contribution-resolution owner QA is explicitly deferred and is not a closure blocker.
- The sweep removed premature ordinary-form access to `FIELD_VERIFIED` for entrances/internal places; Sprint 004 must provide the explicit evidence-based transition.
- Metadata-only routing edits now preserve existing OSM/source provenance and verification state. Geometry/endpoint changes become UNVERIFIED, new records remain MANUAL/UNVERIFIED, and split replacements retain a parent-segment source reference.
- Invalid direct Published reactivation now returns a normal editor message rather than leaking model validation, and duplicate internal aliases are handled as form errors.
- Database inspection found 8 Locations, 9 Entrances, 3 Floors, 3 Internal Places, 49 nodes, 54 segments, 6 entrance anchors and 6 legacy anchors; no routing node or segment is FIELD_VERIFIED.
- Final verification passes with 120 Django and 44 JavaScript tests plus clean system, compilation, syntax, migration-drift and whitespace checks.
- Phase 4 Sprint 003 is OWNER ACCEPTED / CLOSED. Sprint 002 acceptance and detailed contribution-resolution QA remain deferred. Phase 4 remains IN PROGRESS.

---

## Phase 4 — Sprint 004: Path Survey Evidence & Segment Verification

**Status:** IMPLEMENTED — OWNER FIELD REVIEW REQUIRED
**Date:** 2026-09-24

- Added explicit private Path Survey sessions and ordered, accuracy-classified GPS evidence with mobile controls, interruption safety and IndexedDB buffering.
- Added deterministic trace analysis producing revision-bound candidate matches while keeping algorithm classification separate from reviewer disposition.
- Added dedicated review/grant/revoke permissions and append-only verification history; no survey, strong match or completion automatically grants `FIELD_VERIFIED`.
- Added authoritative revision-aware segment mutation, fingerprinting, automatic demotion after material changes and relational split lineage.
- Existing OSM-derived graph records remain UNVERIFIED. No physical survey or field-verification claim has been made.
- Verification passes with 130 Django and 46 JavaScript tests. HTTPS physical-device QA, Sprint 002 acceptance and detailed contribution-resolution QA remain before Phase 4 closure.
- `BUILD_JOURNAL.md` remains unchanged until owner acceptance.

### Phase 4 Pre-Closeout Status Reconciliation — 2026-09-27

- Phase 4 Sprint 002 is formally OWNER ACCEPTED / COMPLETE. Acceptance covers outdoor Places, multiple Entrances, representative-point/entrance separation, Floors, Internal Places and aliases, primary-entrance fallback, explicit routing-entrance override, map-first `EntranceNetworkAnchor` management, editor-approved arrival connectors with bend points, exact physical-entrance route completion and textual indoor handoff without any indoor-routing claim.
- Sprint 002's earlier implementation and correction entries remain unchanged as factual snapshots of their then-current review state.
- Entrance attachment still begins at an existing graph node. When the best connection lies mid-segment, this may create avoidable backtracking; safe segment-aware attachment or transactional splitting is future field-mapping work and is not a Sprint 002 acceptance blocker.
- Phase 4 Sprint 003 remains OWNER ACCEPTED / COMPLETE. Detailed ContributionResolution owner QA remains intentionally deferred.
- Phase 4 Sprint 004 is IMPLEMENTATION COMPLETE / TECHNICAL AUDIT COMPLETE / PHYSICAL OWNER ACCEPTANCE PENDING. It is not owner accepted and Phase 4 is not closed.
- The current full verification baseline is 171 Django tests and 77 JavaScript tests, with Django checks, migration drift, Python compilation, JavaScript syntax and Git whitespace validation clean.
- No current campus path is `FIELD_VERIFIED`; OSM-derived geometry remains `UNVERIFIED` pending explicit physical review.
- Final Phase 4 closure still requires real-device and real-campus field acceptance. Cloudflare Quick Tunnel support remains development-only; no production deployment exists.

### Pre-Deployment Cleanup and Production-Candidate Preparation — 2026-09-27

- Created and integrity-checked an external pre-cleanup SQLite backup before mutation.
- Removed the six fixed-UUID DEMO Locations, their demo/test children and anchors, the explicit Phase 4 test Location, and the owner-approved disposable DEMO Library correction contribution.
- Retained New Building and Sports Complex with all current child data. Both Locations and all five retained entrances remain `UNVERIFIED`; no `FIELD_VERIFIED` status was granted.
- Retained the operational routing graph unchanged at 49 active nodes and 54 active segments, together with four private survey records and 269 raw survey samples.
- Added a dry-run-by-default, repeat-safe cleanup command and a forward migration so fresh production schemas do not finish with historical DEMO seed records.
- Replaced permanent public DEMO presentation with verification-aware data labels while retaining DEMO fixtures, diagnostics and domain states for isolated testing.
- Prepared Render/PostgreSQL environment handling, Gunicorn startup, WhiteNoise static serving, secure production defaults and a lightweight health endpoint. No PostgreSQL transfer, GitHub push, Render resource or deployment has occurred.
- Verification passes with 176 Django tests and 77 JavaScript tests. Phase 4 Sprint 004 physical owner acceptance remains pending; this preparation does not close Phase 4.

---

## Public Map â€” Destination Density & Semantic Zoom Upgrade

**Status:** IMPLEMENTED â€” OWNER REVIEW REQUIRED
**Date:** 2026-09-28

- Replaced always-visible destination points with MapLibre-native GeoJSON clustering at overview and mid zoom, using conservative campus-scale radius and maximum-cluster zoom settings.
- Added compact cluster circles and count labels; clicking/tapping a cluster requests MapLibre's expansion zoom and moves the camera without opening a destination card.
- Retained category-coloured individual markers at close zoom and limited destination text labels to the close-detail range.
- Moved selected-destination rendering to a separate one-feature GeoJSON source so search/category selections remain visible above cluster state and continue using the existing destination panel and Directions flow.
- Preserved the existing search/category `onFilter` pathway: the filtered feature collection replaces the clustered source data and MapLibre reclusters it automatically.
- Established deliberate foreground ordering so active route lines, selected destinations, route endpoints and live-location indicators remain readable above density layers.
- Added eight JavaScript behavior tests. Current verification is 176 Django tests and 85 JavaScript tests passing; owner desktop/mobile visual review remains required.
- No schema, migration, endpoint contract, production database, campus record, routing graph, verification state or deployment resource changed. No commit or push is included.
