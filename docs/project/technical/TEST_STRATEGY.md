# Test Strategy — YCT Map

## Status

```
Current phase:     PHASE 2 — ROUTING & NAVIGATION
Implementation:    FOUNDATIONAL SUITE ACTIVE
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

Coverage includes model validation, aliases, DEMO fixture integrity, map-page configuration, explicit GeoJSON serialization, partial/case-insensitive name search, alias search, category filtering, empty results, invalid input and read-only endpoint behavior.
