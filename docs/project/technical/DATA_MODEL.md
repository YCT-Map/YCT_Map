# Data Model — YCT Map

## Status

```
Current phase:     PHASE 2 — OWNER ACCEPTED
Implementation:    LOCATION, ALIAS, WALKABLE NETWORK, PROVENANCE + LOCATION ANCHOR SUBSET IMPLEMENTED
```

This document describes the expected data model based on approved product decisions.

> **Phase 4 authority notice:** The future-model sketches below predate the owner-approved [`../phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md`](../phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md). For Phase 4 planning, that specification supersedes the sketches wherever they assume one category, one entrance, a building-only parent concept, a simple floor string/count, or moderation that directly publishes data. No Phase 4 model design or migration has begun.

Implemented subsets are identified below; later entities remain design intent.

All field names and types are indicative — actual implementation may differ.

## Current Sprint 001 Implementation

`Location` currently implements UUID identity, name, controlled category, short description, decimal entrance latitude/longitude, controlled verification state, active state and timestamps.

`LocationAlias` provides a one-to-many alias relationship with a per-location uniqueness constraint.

Building geometry, floors, internal locations, paths, contributions and verification-user relationships remain planned and were intentionally not created during Sprint 001.

## Current Phase 2 Implementation

`WalkableNode` stores a stable UUID, optional label, decimal longitude/latitude, controlled verification state, active state and timestamps.

`WalkableSegment` stores a stable UUID, optional label, start/end node foreign keys, GeoJSON `LineString`, bidirectional flag, controlled verification state, active state and timestamps. Distance is derived from geometry rather than stored manually.

The primary local development network contains 47 OSM-derived nodes and 54 segments imported as `UNVERIFIED`. Six synthetic DEMO destinations are connected through explicitly reviewed, non-field-verified anchors. The earlier five-node/five-segment synthetic topology remains only as an isolated automated-test fixture.

`WalkableNode` and `WalkableSegment` retain controlled source provenance: `source_type`, `source_reference`, optional OSM version and optional source timestamp. Provenance identifies where geometry originated; it does not change verification state.

Phase 2 Sprint 002 adds routing-owned `LocationNetworkAnchor`. It currently gives one active location one primary network-node connection. This keeps locations separate from graph junctions and can later evolve to multiple entrances without changing the A* node-to-node contract.

The Medical Centre initially lacked Directions because it had no active `LocationNetworkAnchor`. The OSM realism pass added a deliberate `UNVERIFIED` anchor, so all six DEMO destinations now participate in routing. An anchor expresses a development arrival connection; it does not verify the destination coordinate or entrance in the field.

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
| start_node / end_node | ref:WalkableNode | Graph endpoints |
| geometry | linestring | Geographic path (lat/lng sequence) |
| is_bidirectional | boolean | Whether graph traversal is allowed in both directions |
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

`locations/migrations/0001_initial.py` creates `Location` and `LocationAlias`. Routing migrations create `WalkableNode`, `WalkableSegment` and `LocationNetworkAnchor`. Synthetic records are loaded from explicit fixtures rather than embedded in migrations.

Never rewrite an already-applied migration. Correct data issues through new migrations.

---

## Open Questions

- Exact PostgreSQL spatial representation or extension to use for each geographic field
- Exact PostgreSQL migration and spatial-extension timing

Demo seed loading is resolved for Sprint 001 through an explicit fixture. Demo records use the `DEMO` state and remain removable without changing the production data model.
