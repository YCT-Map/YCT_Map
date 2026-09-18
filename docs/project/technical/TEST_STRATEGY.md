# Test Strategy — YCT Map

## Status

```
Current phase:     PHASE 3 — SPRINT 001 OWNER ACCEPTED
Implementation:    PHASE 2 REGRESSIONS + LIVE-LOCATION BEHAVIOUR SUITE ACTIVE
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

Coverage includes model validation, aliases, DEMO fixture integrity, map-page configuration, explicit GeoJSON serialization, partial/case-insensitive name search, alias search, category filtering, empty results, invalid input and read-only endpoint behavior.
