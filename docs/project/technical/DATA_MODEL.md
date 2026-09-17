# Data Model — YCT Map

## Status

```
Current phase:     PRE-BUILD / FOUNDATION
Implementation:    NOT STARTED
```

This document describes the expected data model based on approved product decisions.

Nothing here is implemented. This is design intent to be validated when the build phase begins.

All field names and types are indicative — actual implementation may differ.

---

## Core Entities

### Location (Physical)

Represents a navigable physical campus destination.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| name | string | Official name |
| aliases | string[] | Alternative search names |
| category | enum | building, school, gate, hostel, library, sports, food, medical, admin, other |
| description | string | Optional brief description |
| entrance_point | coordinates | Primary arrival point (lat/lng) |
| geometry | polygon | Building/area outline — irregular polygons supported |
| floor_count | integer | Optional — number of floors |
| verification_state | enum | DEMO, UNVERIFIED, FIELD_VERIFIED |
| verified_by | ref:Editor | Who verified; null if not verified |
| verified_at | timestamp | When verified |
| created_at | timestamp | |
| updated_at | timestamp | |

**Invariants:**
- A location must have at least a name and an entrance point to be usable for routing.
- DEMO records must never be shown as FIELD_VERIFIED in any user-facing context.
- Do not delete locations with associated verified historical data — mark inactive instead.

### Internal Location

Represents a destination inside a physical building (department, office, classroom, etc.).

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| name | string | |
| parent_location_id | ref:Location | Parent building |
| floor | string | Floor identifier (e.g., "Ground", "1st", "2nd") |
| room_number | string | Optional |
| description | string | Optional |
| verification_state | enum | DEMO, UNVERIFIED, FIELD_VERIFIED |
| created_at | timestamp | |
| updated_at | timestamp | |

**Note:** Internal locations do not have independent outdoor GPS coordinates in V1.

### Path (Walkable Segment)

Represents a walkable path segment within campus.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| geometry | linestring | Geographic path (lat/lng sequence) |
| surface_type | enum | Optional — paved, unpaved, steps, etc. |
| is_accessible | boolean | Optional |
| verification_state | enum | DEMO, UNVERIFIED, FIELD_VERIFIED |
| created_at | timestamp | |
| updated_at | timestamp | |

**Invariants:**
- Paths must not cross buildings, walls, fences or restricted areas.
- Path distances are calculated from geometry — not manually entered.

### Contribution (Public Submission)

Represents an unverified submission from a public user.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| type | enum | NEW_LOCATION, CORRECTION, NEW_PATH |
| submitted_data | json | Flexible — type-dependent |
| submitter_notes | string | Optional |
| status | enum | PENDING, APPROVED, EDITED_APPROVED, REJECTED, FLAGGED, MERGED |
| reviewed_by | ref:Editor | Null until reviewed |
| reviewed_at | timestamp | Null until reviewed |
| created_at | timestamp | |

**Note:** Contributions are archived on rejection — not permanently deleted.

### Editor / Admin User

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| email | string | Login identifier |
| role | enum | EDITOR, ADMIN |
| is_active | boolean | |
| created_at | timestamp | |
| last_login_at | timestamp | |

Authentication uses Django's built-in user and permission system. Editor accounts are admin-managed and invite-only (DEC-T06, DEC-T09).

---

## Verification State Rules

| State | Meaning | Who Can Set |
|-------|---------|-------------|
| DEMO | Demonstration/seed data | System / migration |
| UNVERIFIED | Exists in the system but not field-confirmed | System on submission |
| FIELD_VERIFIED | Physically confirmed by trusted team member | Editor / Admin only |

Promotion from UNVERIFIED to FIELD_VERIFIED requires deliberate editor action after physical confirmation. It must never happen automatically.

---

## Sensitive Fields

- Editor email addresses are private.
- No passwords stored in plain text.
- No PII from public contributors is required (contributions are anonymous).

---

## Migrations

No migrations exist yet. This section must be updated when the first migration is written.

Never rewrite an already-applied migration. Correct data issues through new migrations.

---

## Open Questions

- Exact PostgreSQL spatial representation or extension to use for each geographic field
- Exact seed-loading mechanism for synthetic demonstration data

These are implementation details to resolve within the approved architecture. Regardless of mechanism, demo records must use the explicit `DEMO` state and remain removable without changing the production data model.
