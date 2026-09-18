# API Contract — YCT Map

## Status

```
Current phase:     PHASE 1 — FOUNDATION & MAP EXPERIENCE
Implementation:    PUBLIC LOCATION AND ROUTING ENDPOINTS IMPLEMENTED
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

### `GET /api/locations/`

Public, unauthenticated, read-only location collection.

Optional query parameters:

- `q` — case-insensitive partial match against destination names and aliases; maximum 100 characters
- `category` — controlled category value

The response is an explicit GeoJSON `FeatureCollection`. Each feature exposes only:

- ID
- point coordinates
- name
- controlled category value and label
- description
- verification value and label
- aliases

Inactive locations are excluded. Unknown categories and overlong queries return HTTP 400. Non-GET methods return HTTP 405.

### `GET /api/routes/`

Calculates a route between two active anchored destination UUIDs supplied as `origin` and `destination`. The narrow response contains route geometry, endpoint names, geometry-derived distance, approximate ETA and verification context; graph internals are not exposed.

### `POST /api/routes/from-position/`

Calculates a route from an ephemeral live-position match to an active anchored destination. The JSON body contains `destination` plus `position.latitude`, `position.longitude` and `position.accuracy_metres`. CSRF protection is required. Unsafe accuracy or network matches fail explicitly. The response does not separately echo or persist the submitted coordinate and is marked `Cache-Control: no-store`.

---

## Planned API

To be documented as each sprint produces implemented, tested routes.

## Anonymous contributions (Phase 3 Sprint 004)

`POST /api/contributions/` accepts JSON with `request_id`, `type`, optional `target_location`, `proposed_name`, `proposed_category`, `context`, `description` and optional `proposed_point` (`latitude`, `longitude`). The request requires the standard Django CSRF token. Successful creation returns HTTP 201 with only `id`, `status` and a review message; an idempotent replay returns HTTP 200 with `duplicate_request: true`.

Errors use narrow codes: `INVALID_TYPE`, `INVALID_TARGET`, `INVALID_COORDINATE`, `VALIDATION_ERROR`, and `RATE_LIMITED` (HTTP 429 with `Retry-After`). Submitted data is always pending and this endpoint never edits public campus records.
