# Test Strategy — YCT Map

## Status

```
Current phase:     PRE-BUILD / FOUNDATION
Implementation:    NOT STARTED
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

Django's test facilities are the approved backend baseline. Any additional test runner, browser-testing tool, formatter or static-analysis tool is a Sprint 001 implementation detail and must be recorded after selection.

This section will be updated once the backend and frontend stacks are confirmed.

---

## Current Test Totals

No tests exist yet. This section will record pass/fail totals after the first test suite is established.
