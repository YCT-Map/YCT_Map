# API Contract — YCT Map

## Status

```
Current phase:     PRE-BUILD / FOUNDATION
Implementation:    NOT STARTED
```

This document will describe all API endpoints once the backend is implemented.

The backend uses Django and REST-style APIs. Exact routes are documented only after implementation.

---

## Confirmed API Decisions

- Normal users (unauthenticated) may access: campus location data, search, routing, contribution submission.
- Editor operations require authenticated requests.
- No PII is collected from public contributors.

---

## API Style

REST, implemented with the approved Django backend (DEC-T02).

---

## Planned Endpoint Groups

The following groups are expected based on the product specification. Exact routes will be documented during implementation.

| Group | Audience | Authentication |
|-------|----------|---------------|
| Locations | Public | None |
| Search | Public | None |
| Routing | Public | None |
| Contributions | Public | None |
| Editor — Locations | Editors | Required |
| Editor — Contributions | Editors | Required |
| Editor — Paths | Editors | Required |
| Admin — Users | Admins | Required |

---

> Do not document routes here until they are actually implemented.
> Do not invent future endpoints.
> Keep CURRENT and PLANNED sections clearly separated.

---

## Current API

No endpoints exist yet.

---

## Planned API

To be documented as each sprint produces implemented, tested routes.
