# Test Strategy — YCT Map

## Status

```
Current phase:     PHASE 1 — FOUNDATION & MAP EXPERIENCE
Implementation:    FOUNDATIONAL SUITE ACTIVE
```

This document defines the intended testing approach for YCT Map.

Specific test and static-analysis tools will be recorded when the Django and frontend foundations are implemented.

---

## Test Categories

| Category | Purpose | Status |
|----------|---------|--------|
| Unit tests | Test individual functions and components in isolation | NOT STARTED |
| Integration tests | Test interactions between components and with the database | NOT STARTED |
| End-to-end tests | Test full user flows against a running application | NOT STARTED |
| Regression tests | Prevent previously fixed issues from recurring | NOT STARTED |
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

Sprint 001: 12 Django tests passing.

Coverage includes model validation, aliases, DEMO fixture integrity, map-page configuration, explicit GeoJSON serialization, partial/case-insensitive name search, alias search, category filtering, empty results, invalid input and read-only endpoint behavior.
