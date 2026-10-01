# Test Strategy — YCT Map

## Status

```
Current phase:     PHASE 4 SPRINT 004 — PHYSICAL OWNER ACCEPTANCE PENDING
Implementation:    COMPLETE PHASE 1–4 TECHNICAL REGRESSION SUITE ACTIVE
```

This document defines the intended testing approach for YCT Map.

Specific test and static-analysis tools will be recorded when the Django and frontend foundations are implemented.

---

## Test Categories

| Category | Purpose | Status |
|----------|---------|--------|
| Unit tests | Test individual functions and components in isolation | ACTIVE |
| Integration tests | Test interactions between components and with the database | ACTIVE |
| End-to-end tests | Test full user flows against a running application | MANUAL BROWSER BASELINE |
| Regression tests | Prevent previously fixed issues from recurring | ACTIVE |
| Production smoke tests | Verify a deployment is alive and serving correctly | NOT STARTED |

---

## Intended Coverage

| Area | Approach |
|------|----------|
| Routing algorithm | Unit + integration tests with demo data |
| Search functionality | Integration tests |
| Location management (editor) | Integration + E2E tests |
| Contribution submission | Integration + E2E tests |
| Authentication (editor login) | Integration tests |
| Map rendering | E2E tests (visual/behavioral) |
| Distance / time calculation | Unit tests |

---

## Required Gates

### Before Commit
- Focused tests pass
- Typecheck passes
- No secrets in diff

### Before Merge
- Relevant regression tests pass
- Full test suite passes
- Build passes
- Linter / static checks pass

### Before Deployment
- All merge gates satisfied
- Production smoke test defined and passing
- Rollback plan confirmed

---

## Demo Data in Tests

Tests may use demonstration/seed data.

Tests must not mark demo data as FIELD_VERIFIED.

Tests must not depend on invented real YabaTech coordinates being accurate.

---

## Framework

Django's built-in test framework is the current automated baseline. JavaScript syntax is checked with Node's built-in `--check`; browser behavior is verified against the running application in Chromium/Chrome.

---

## Current Test Totals

Sprint 001: 12 Django tests passed at acceptance.

Sprint 002: 13 Django tests passing, including validation of the approved OSM campus-orientation asset and its page configuration. Live browser checks cover campus framing, the return-to-campus control, category browsing, selection, mobile layout, keyboard focus, reduced motion, touch targets and graceful degradation when either the map module or style is unavailable.

Phase 2 Sprint 001: 23 Django tests passed at acceptance. Routing coverage includes DEMO fixture integrity, curved LineString length, zero-length rejection, self-edge rejection, endpoint anchoring, bidirectional reverse arcs, inactive-segment exclusion, reverse-duplicate diagnostics, the DEBUG inspection contract and its production exclusion. Owner verification covered node/segment rendering, the toggle, the “no route calculated” state, the corrected campus label and Phase 1 discovery regressions.

Phase 2 Sprint 002: 45 Django tests passed at acceptance. New coverage includes direct and multi-arc A*, shortest-distance-over-fewer-hops selection, deterministic ties, reconstruction, unreachable and same-origin behavior, one-way traversal, inactive nodes, reversed/continuous geometry, junction deduplication, baseline ETA, DEMO anchors, missing/inactive anchors, node-only routing and narrow DEBUG contracts. Owner verification confirmed origin/destination selection, distinct route rendering, distance, ETA, multiple inspection states and earlier-sprint regressions.

Phase 2 Sprint 003: 48 Django tests pass before owner review. New contract coverage verifies routing availability, the user Directions entry point, production-page DEBUG isolation, the narrow public route result, graph-internal exclusion, same-origin handling and missing-anchor handling. Manual browser verification covers responsive route sheets, static endpoint clarity, route visibility, clear/change states and regressions.

Sprint 003 owner-review correction: 49 Django tests pass. Cache-version coverage now prevents current Sprint 003 markup from being combined with stale JavaScript modules. A fresh mobile-browser run verifies destination selection, visible Directions, the independent user route form, closed Developer tools, route calculation, endpoint-aligned blue `S`/red `D` markers, distance, approximate ETA and change/clear controls.

Sprint 003 second owner-review correction: 49 Django tests and 3 Node-executed JavaScript behaviour tests pass. The JavaScript suite executes destination-card Directions emission, choosing-origin state, destination exclusion, origin selection, the public route request/result callback, route-summary rendering, cancellation and clearing. A fresh Microsoft Edge mobile trace additionally verifies correction-2 asset delivery, four eligible origin UUIDs plus the empty placeholder, `route-available` application state, closed Developer tools and the blue public route with endpoint-aligned `S`/`D` markers.

OSM network realism pass: 52 Django tests and 3 JavaScript behaviour tests pass. New tests cover deterministic reviewed-snapshot conversion, provenance, restriction rejection, transactional replacement, 47-node/54-segment persistence, six anchors and Medical Centre routing availability. All fifteen destination pairs are routable in the loaded development graph.

Phase 2 final acceptance retains those 52 Django and 3 JavaScript behaviour tests as the milestone baseline. Backend/static checks alone did not catch the owner-visible Sprint 003 transition problem, so behavior-level JavaScript tests now execute the destination-to-navigation state flow, cancellation and clearing rather than checking only source strings or response markup.

Phase 3 Sprint 001 implementation: 52 Django tests and 8 Node-executed JavaScript tests pass. New coverage validates malformed samples, accuracy quality, stale samples, noisy jumps, trustworthy heading, unsupported browsers, watcher cleanup including permission revocation, permission denial, marker callbacks, recentering and stop behavior. Browser simulation and later physical-phone GPS verification remain separately reported.

Owner acceptance records `SIMULATED GEOLOCATION VERIFIED`. It does not record physical-phone GPS verification. The owner also confirmed that an accepted approximately 40 m position remains displayed when a substantially worse approximately 100 m sample arrives.

Phase 3 Sprint 002 acceptance: 60 Django tests and 12 Node-executed JavaScript tests pass. Server coverage includes complete-polyline projection, preferred/caution snap thresholds, poor-accuracy and excessive-distance rejection, ephemeral graph augmentation, one-way behavior, CSRF enforcement and the narrow no-store response. Client coverage includes the live POST contract, route projection, stable backward progress, stationary handling, confirmed arrival and filtered personal-speed ETA. The owner visually verified live-origin routing, safe snapping, progress, remaining distance and personal-pace ETA. Stationary and arrival transitions remain deterministic automated verification rather than owner-observed verification.

Phase 3 Sprint 003 implementation: 60 Django tests and 23 Node-executed JavaScript tests pass before owner review. New deterministic coverage checks bounded accuracy-aware corridors, a single anomaly with recovery, poor-accuracy uncertainty, repeated reliable deviation, backtracking, arrival precedence, cooldown/movement gating, an active-graph-derived off-route trace, no-false-reroute GPS degradation, one route replacement, pace preservation and retained-route failure with retry. The existing Django live-origin endpoint remains the authoritative reroute service and its matching/privacy tests remain green.

Owner acceptance visually confirms the off-route checking state, one controlled reroute, route/destination replacement semantics, post-reroute progress and camera preservation. Automated verification remains the authority for exact confirmation timing, anomaly recovery, poor-GPS behavior, request locking, stabilization, cooldown, movement gating, failure handling, pace preservation and arrival precedence. The verification label is `SIMULATED REROUTING VERIFIED`, not physical-device verification.

Phase 3 Sprint 004 implementation: 70 Django tests and 27 Node-executed JavaScript tests pass before owner review. Contribution coverage includes anonymous pending submission, validation, bounded text, safe treatment of script-like text, no public-location mutation, CSRF, rate limiting, UUID replay protection, staff-only moderation and review audit fields. Frontend coverage includes opening and adapting the form, narrow protected submission, success feedback, retry with retained data/idempotency key and explicit point selection/removal. The complete earlier search, routing, live-navigation and rerouting suites remain green.

Phase 3 final acceptance: 74 Django tests and 34 Node-executed JavaScript tests pass. The final additions cover real MapLibre coordinate precision, client/server six-decimal normalization, coordinate-specific errors, accepted-submission quota separation, bounded invalid traffic, idempotent quota behavior, responsive mobile contracts and route-state preservation across foreground panels. Owner verification covers contribution submission, map points, pending moderation, approval/rejection and audit behavior, unchanged public data after moderation, manual-route regression and the approximately 360×800 mobile route layout. Physical-phone navigation/rerouting remains unverified.

Phase 4 Sprint 001 acceptance: 94 Django tests and 34 Node-executed JavaScript tests pass. New coverage includes login success/failure, safe redirects, POST logout, CSRF enforcement, inactive users, least-privilege Editor permissions, direct-request authorization, Draft creation, multiple controlled categories, typed aliases, local alias collision rules, archive/reactivation, publication completeness, server-set audit actors, seeded taxonomy, preserved DEMO UUIDs and public exclusion of Draft/Archived places. Owner verification covered login, the custom place UI, coordinate-free Draft creation, physical type, multiple categories, typed aliases, public exclusion and existing DEMO search/navigation/manual routing. The remaining detailed branches are automated-test verification.

Phase 4 Sprint 002 implementation verification: 100 Django tests and 34 Node-executed JavaScript tests pass before owner review. Added coverage proves that published outdoor/internal destinations remain public with routing disabled, internal search and floor-grouped directory behavior, same-parent validation, the one-active-primary database invariant and entrance-anchor routing readiness. JavaScript syntax, Django system checks and migration drift are clean.

Phase 4 Sprint 002 owner-test correction verification: 107 Django tests and 36 Node-executed JavaScript tests pass. Regression coverage now renders a place detail after floor creation, reverses and opens the nested floor-edit route, enforces parent ownership, edits a floor without changing its UUID, reports duplicate levels inline, verifies entrance-selector markup and hidden coordinate fields, persists valid points, rejects missing points, initializes saved points and exercises marker repositioning in JavaScript.

Phase 4 Sprint 003 adds server tests for the field-capture DOM contract, protected primary-entrance overwrite, repeatable approved contribution resolutions, connected-node movement rejection and history-preserving transactional splits. JavaScript tests cover checkbox alignment, one-shot accuracy-aware field capture and endpoint-preserving segment drawing. Visual MapLibre interaction remains owner/Antigravity browser QA; no custom browser harness is added.

Phase 4 Sprint 003 closure verification passes with 120 Django and 44 Node-executed JavaScript tests. Stability additions cover invalid direct reactivation without a 500, non-editable verification before an evidence workflow, duplicate internal aliases as form errors, OSM provenance preservation on metadata edits and split-parent lineage. The owner verified representative-map loading/placement/persistence, responsive current-location behavior including rejection near 212 m accuracy, and retained entrance/floor/internal-place workflows. Detailed contribution-resolution owner QA remains deferred.

Phase 4 Sprint 004 implementation verification passes with 130 Django and 46 Node-executed JavaScript tests. New deterministic coverage includes lifecycle/ownership, private evidence access, accuracy/outlier/stationary classification, idempotent batches, immutable completed samples, exact/no-candidate matching, revision-bound grants, low-coverage override, revocation permissions, material-edit invalidation and relational split lineage. JavaScript verifies accuracy bands, active-only collection, IndexedDB use and non-automatic interrupted recovery. Physical phone GPS and real segment verification remain owner/staging acceptance work.

The local survey-UI correction increases verification to 132 Django and 48 JavaScript tests. Persisted-classification summaries prove rejected samples increase raw/rejected counts without increasing usable count; accepted and weak samples are usable. Timing coverage proves explicit active accumulation, pause/refresh stability, prospective resume and separately labelled wall-clock duration.

The ACTIVE/PAUSED field-map addition increases verification to 133 Django and 49 JavaScript tests. Coverage proves persisted usable coordinates alone form the trace, rejected evidence is retained but omitted from visualization, synchronized trace data survives pause, the active graph is supplied read-only and map failure copy explicitly preserves recording/synchronization behavior.

Development-only Cloudflare Quick Tunnel configuration increases the Django total to 135. Focused coverage proves the `.trycloudflare.com` host/origin wildcard is produced for development, excluded from production and does not remove localhost support.

The Phase 4 hardening, GPS/matching and exact-arrival corrections bring the current full baseline to **171 Django tests and 77 Node-executed JavaScript tests**. Added server coverage includes accuracy/time-aware survey downsampling, nearby contiguous candidate coverage, candidate-noise treatment, route coordinate contracts, entrance connection integrity, exact connector endpoints, connector-derived distance/ETA, legacy null connectors, explicit/fallback internal-place entrances and preserved textual handoff. Added frontend coverage includes public-location stabilization and quality wording, mobile HUD/menu/route layout, field-map evidence trace behavior, editor connector bend controls, exact-entrance route bounds and live/manual internal handoff semantics.

The current static gate also passes Django system checks, migration-drift checks through routing migration `0009`, Python compilation, JavaScript syntax checks and Git whitespace validation. These results establish technical readiness, not physical owner acceptance. No test marks a campus path `FIELD_VERIFIED`, and real-device survey acceptance remains pending.

The public-map Destination Density & Semantic Zoom upgrade raises the JavaScript total to **85** while the full Django suite remains **176**. The eight focused tests verify native cluster configuration, cluster/unclustered layer filters, close-zoom labels, independent selected-destination rendering, search/category source updates, cluster expansion without accidental selection, graceful expansion failure and foreground ordering for routes, endpoints and live location. Visual density, mobile tap behavior and label readability remain owner browser checks.

Coverage includes model validation, aliases, DEMO fixture integrity, map-page configuration, explicit GeoJSON serialization, partial/case-insensitive name search, alias search, category filtering, empty results, invalid input and read-only endpoint behavior.

The Field-Test Stabilization sprint raises the JavaScript total to **94** while the full Django suite remains **176**. New behavior coverage verifies the route-origin radio-card contract, route-eligible filtering, destination exclusion, live-state and staleness presentation without chooser rebuilding, newer-position-only recovery, single-request locking, the three-attempt bound, non-retryable failures, all cancellation paths and duplicate-submit/loading cleanup. Server-rendered coverage confirms the public native route-origin select is absent. Physical Samsung/Edge compositor behavior and live network matching remain owner field checks.

The Navigation Orientation & Follow Mode sprint raises the JavaScript total to **103** while the full Django suite remains **176**. Focused coverage verifies normalization and screen rotation, north-crossing circular smoothing, isolated-jump damping, device/movement/stale priority, permission denial and unsupported fallback, listener lifecycle, marker position independence, follow suspension/resumption, north-up reset and mobile/desktop look-ahead layout. Physical compass quality, sensor interference and walking-camera behavior remain Samsung/Edge owner checks.

The Campus-First Map Redesign raises the JavaScript total to **108** while the full Django suite remains **176**. Five focused tests verify that the outside-context mask is derived without mutating the approved campus polygon, the campus interior remains a polygon hole, camera constraints use zoom 15–20 with an approximately 400 m geometry-derived buffer, the interactive/navigation layer order is deliberate, compatible Liberty layers are discovered by source/type rather than fixed IDs, and unsupported optional style changes fail safely. The complete clustering, GPS, live-navigation, rerouting, route-rendering, menu and responsive suites remain green. Visual contrast, approach-road readability and Samsung-sized framing remain owner browser checks.

The YCT Map Visual Identity + Destination Density Polish raises the JavaScript total to **110** while the Django baseline remains **176**. Expanded tests verify the 24% polygon-derived interior canvas, unchanged boundary geometry, source/type-discovered foreground land/building/path layers, non-extruded source-backed close-zoom shadow, safe optional-layer failure, exact 4/5/6 px destination radii, separate 15 px-radius cluster-excluding hit targets, reduced 15/18/21 px clusters, label-first zoom thresholds and hit-layer-only pointer selection. Search selection, category reclustering, independent selected destination, cluster expansion and the complete navigation/location suites remain green. Final physical contrast, tap comfort and non-zero-bearing appearance remain owner device checks.

The owner-directed Campus Core Camera + Liberty Detail Restoration correction raises the JavaScript total to **112** while the Django baseline remains **176**. Camera coverage verifies the approved centre, desktop/mobile core profiles, fallback and clamp behavior, separate overview framing, initial-load/Home ownership, zoom/context constraints and route/destination/follow independence. Presentation coverage verifies that YCT now adds only its orientation overlays, that the boundary uses the approved zoom-responsive width/opacity values, and that runtime Liberty POI/building/path mutations, the outside mask, ivory canvas and building shadow are absent. Native Liberty label placement and final responsive framing remain owner browser checks.

The local Checkpoint Hierarchy + Flexible Live Navigation build raises verification to **178 Django tests and 115 JavaScript tests**. Server coverage proves the checkpoint default, editor checkbox persistence and explicit public GeoJSON property without coupling the flag to publication, verification or routing. Map tests prove checkpoint-only permanent markers, ordinary label/hit behavior, unchanged clustering and selected overlays. Navigation tests cover pure geographic route slicing at start/mid-leg/vertex/end/degenerate geometry, immutable inputs, trustworthy progress emission, uncertainty freezing, deliberate confirmed backtracking, marker-only heading and one-shot bearing-preserving recentering. Physical Samsung/Edge behavior and checkpoint visual hierarchy remain owner checks; the migration exists locally but has not been applied to the current database.

The local Field Mapping, Heading, GPS Capture and Evidence-Based Path Verification integration raises verification to **201 Django tests and 122 JavaScript tests**. Heading coverage includes tilt-aware physical N/E/S/W transformation, screen-orientation correction, map-bearing-relative rendering, missing-sensor fallback and marker/camera separation. Location coverage proves campus/context inclusion, far-away rejection, public non-render/non-camera behavior, fail-closed boundary configuration and shared five-second editor capture lifecycle. Server coverage proves independent permission-gated Place/Entrance verification, coordinate-change demotion, chronological pass detection, conservative existing-segment promotion, no auto-revocation, candidate discovery, one-versus-two-pass trust, read-only graph preview, duplicate protection and transactional splitting. Review-map tests cover human candidate IDs, candidate focus and confirmation-only filtering. The whole-campus backup dry run remains separate from these test databases and performs no writes.
