# Data Model — YCT Map

## Status

```
Current phase:     PHASE 4 SPRINT 004 — PHYSICAL OWNER ACCEPTANCE PENDING
Implementation:    PATH SURVEY EVIDENCE + REVISION-BOUND SEGMENT VERIFICATION TECHNICALLY COMPLETE
```

This document describes the expected data model based on approved product decisions.

> **Phase 4 authority notice:** The owner-approved [`../phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md`](../phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md) is authoritative. Sprints 001–003 are owner accepted. Sprint 004 field tooling is implemented and technically audited; physical owner field acceptance remains pending.

## Current Phase 4 Sprint 004 Implementation

`PathSurvey` owns the explicit Draft/Active/Paused/Completed/Reviewed/Abandoned lifecycle. `PathSurveySample` stores only survey coordinates, timestamps, accuracy, ordering and optional movement metadata; completed evidence is immutable and protected from destructive cascading deletion. Draft and abandoned records have a 30-day policy, completed/unreviewed records 90 days, and reviewed verification evidence is retained; automatic deletion/compaction is not implemented in this sprint.

`active_capture_seconds` is a prospective monotonic accumulator updated only while an editor has explicitly started the browser GPS watcher. `active_capture_tracking_started` distinguishes newly measured surveys from pre-correction history. Wall-clock session duration remains a separate derived `started_at` to `completed_at` value; paused or interrupted time is never labelled active capture.

`SurveySegmentMatch` binds an algorithm conclusion (`STRONG`, `PARTIAL`, `AMBIGUOUS`, `DISCREPANCY`) to one segment revision and fingerprint. Reviewer disposition is separate. A survey with no meaningful candidate has no artificial match row. `SegmentVerificationRecord` is append-only history for explicit grants, revocations and invalidation after material mutation.

`WalkableSegment.geometry_revision` and `geometry_fingerprint` make verification belong to exact geometry. Material endpoint, LineString or directionality edits pass through the transactional mutation service, increment revision, recompute the fingerprint and demote current verification while preserving history. Split replacements use a relational `derived_from_segment` link and remain UNVERIFIED.

## Current Phase 4 Sprint 002 Implementation

`Entrance` has stable UUID identity, a parent Location, custom name, controlled broad type, required point, active/primary flags, independent verification and audit fields. A conditional database constraint permits at most one active primary entrance per Location. Zero entrances remains valid for published records, but routing is then unavailable.

`Floor` is a signed numeric level plus editable label/display order and active state, unique by parent and level. `InternalPlace` has stable UUID identity, controlled type, parent, optional floor while Draft, room/wing/direction metadata, optional same-parent routing entrance, publication state, verification and audit fields. Published internal places require an active same-parent floor, but not a route-ready entrance. `InternalPlaceAlias` preserves independent searchable aliases without changing outdoor aliases.

`EntranceNetworkAnchor` connects an Entrance to one active WalkableNode. Its nullable `connector_geometry` stores an explicitly approved GeoJSON LineString from that node to the exact Entrance point. Connector distance is derived from geometry; null preserves an explicit legacy node-only arrival without fabricating geometry. New or edited connectors remain `UNVERIFIED`. A destination advertises routing only when resolution produces a valid active arrival entrance and anchor (or the explicitly temporary legacy fallback). Publication and `FIELD_VERIFIED` status neither imply nor are implied by routing readiness.

Implemented subsets are identified below; later entities remain design intent.

All field names and types are indicative — actual implementation may differ.

## Current Phase 4 Sprint 001 Implementation

`Location` remains the stable UUID outdoor-place identity. It now includes a controlled physical place type, multiple functional `Category` records, Draft/Published/Archived publication state, nullable representative coordinates, independent verification state, nullable creator/updater actors and timestamps. The default-false `is_checkpoint` flag is a presentation-only editor decision for prominent wayfinding landmarks; it does not change publication, verification, routing readiness or category.

`LocationAlias` retains its one-to-many relationship and adds controlled alias kinds. Alias names are case-insensitively unique only within one place; the same alias may identify multiple places in search.

The legacy `Location.category`, `entrance_latitude` and `entrance_longitude` fields are intentionally retained as deprecated compatibility fields through Sprint 001. Existing records were backfilled into the new category relation and representative point. New editor/domain behavior treats the new fields as authoritative. Representative points are not routing entrances.

Only complete `PUBLISHED` places enter the public API. Draft and Archived records remain editor-only. Publication state remains independent from `DEMO`, `UNVERIFIED` and `FIELD_VERIFIED`.

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
| aliases | relation | Typed `LocationAlias` records |
| categories | many-to-many | Controlled functional discovery categories |
| place_type | enum | Controlled physical classification |
| publication_status | enum | DRAFT, PUBLISHED, ARCHIVED |
| description | string | Optional brief description |
| representative point | coordinates | Map/search presentation point; not an Entrance |
| is_checkpoint | boolean | Prominent map-landmark presentation only; default false |
| entrances | relation | Zero or more separately managed physical arrival points |
| geometry | polygon | Building/area outline — irregular polygons supported |
| floor_count | integer | Optional — number of floors |
| verification_state | enum | DEMO, UNVERIFIED, FIELD_VERIFIED |
| verified_by | ref:Editor | Who verified; null if not verified |
| verified_at | timestamp | When verified |
| created_at | timestamp | |
| updated_at | timestamp | |

**Invariants:**
- A Location requires a representative point before publication, but routing availability depends separately on valid Entrance/anchor resolution.
- DEMO records must never be shown as FIELD_VERIFIED in any user-facing context.
- Do not delete locations with associated verified historical data — mark inactive instead.

### InternalPlace

Represents a destination inside a physical building (department, office, classroom, etc.).

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| name | string | |
| location_id | ref:Location | Parent outdoor Place |
| floor | ref:Floor | Optional while Draft; active same-parent Floor required when Published |
| room_code | string | Optional room/code |
| wing | string | Optional wing/section |
| direction_note | string | Textual indoor handoff guidance |
| routing_entrance | ref:Entrance | Optional active same-parent override; otherwise primary fallback |
| publication_status | enum | DRAFT, PUBLISHED, ARCHIVED |
| description | string | Optional |
| verification_state | enum | DEMO, UNVERIFIED, FIELD_VERIFIED |
| created_at | timestamp | |
| updated_at | timestamp | |

**Note:** Internal Places do not have independent outdoor GPS or indoor route geometry in V1. Routes end at an Entrance and preserve textual handoff fields.

### Path (Walkable Segment)

Represents a walkable path segment within campus.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| start_node / end_node | ref:WalkableNode | Graph endpoints |
| geometry | linestring | GeoJSON coordinates in `[longitude, latitude]` order |
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

`locations/migrations/0001_initial.py` creates the historical `Location` and `LocationAlias` schema. `0002_campus_place_foundation.py` and `0003_seed_and_backfill_campus_places.py` establish Sprint 001. `0004_entrance_floor_internalplace_internalplacealias_and_more.py` adds Sprint 002 domain records. Routing `0004_entrancenetworkanchor.py` adds entrance anchoring and `0005_backfill_demo_entrances.py` creates one compatible primary entrance per existing anchored DEMO destination without changing UUIDs or graph nodes.

Sprint 003 adds nullable, history-preserving routing `created_by`/`updated_by` actors in routing migration `0006`, and repeatable `ContributionResolution` audit actions in contributions migration `0002`. A resolution points to exactly one affected campus record (or none for an explicit no-change action). Approval, resolution, publication, verification and routing availability remain independent states.

Routing migration `0007` adds segment revision/fingerprint and verification-history foundations. Migration `0008` adds prospective active-capture timing and related Path Survey evidence fields. Migration `0009_entrancenetworkanchor_connector_geometry.py` adds only nullable arrival-connector geometry and preserves every existing anchor as legacy node-only until an editor explicitly confirms a connector.

Locations migration `0006_location_is_checkpoint.py` adds the default-false checkpoint presentation flag. It contains no data operation and does not select or alter the trust state of any existing place. It remains unapplied to the current local SQLite database until owner review.

Never rewrite an already-applied migration. Correct data issues through new migrations.

---

## Open Questions

- Exact PostgreSQL spatial representation or extension to use for each geographic field
- Exact PostgreSQL migration and spatial-extension timing

Demo seed loading is resolved for Sprint 001 through an explicit fixture. Demo records use the `DEMO` state and remain removable without changing the production data model.
