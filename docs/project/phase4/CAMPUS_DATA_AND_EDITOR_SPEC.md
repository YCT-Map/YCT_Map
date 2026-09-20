# YCT Map — Campus Data & Editor Specification

**Recommended repository path:** `docs/project/phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md`
**Status:** Approved Phase 4 design baseline
**Purpose:** Define how YCT Map represents real YABATECH places and how trusted editors collect, structure, and maintain campus data before Phase 4 implementation begins.

---

## 1. Purpose

YCT Map is not only a map of buildings.

The real campus contains buildings, halls, lecture rooms, laboratories, offices, libraries, food hubs, sports facilities, medical facilities, administrative places, gates, and other useful destinations. Phase 4 must therefore provide a flexible campus-place model rather than forcing every destination into a single `Building` concept.

This specification defines:

- outdoor campus places;
- place types and categories;
- aliases, abbreviations, and examination codes;
- entrances;
- internal places;
- floors;
- editor authentication;
- field-capture workflow;
- map placement;
- internal-place population;
- building/place directories;
- routing behavior for internal destinations;
- Phase 5 field-mapping workflow.

It is the authoritative Phase 4 product/data contract unless the owner explicitly changes it later.

---

## 2. Core Principles

1. **Not everything is a building.**
2. **Outdoor routable places and internal places are different concepts.**
3. **Searchability does not require a permanent visible map marker.**
4. **A place's representative point is not necessarily its routing entrance.**
5. **Multiple entrances must be supported.**
6. **One entrance may be designated as the primary routing entrance.**
7. **Internal destinations do not require indoor route geometry.**
8. **Codes and abbreviations are searchable aliases, not record identity.**
9. **Editors should work through map/current-location capture, not raw coordinates.**
10. **The editor workflow should match real field work on campus.**
11. **OSM-derived routing remains distinct from YCT Map-owned campus data.**
12. **Moderation approval is not the same as field verification.**

---

## 3. Campus Place Model

### 3.1 Outdoor Place

An outdoor place is a physically identifiable campus destination that can have a map representation and may be directly routable.

Examples include Science Complex, College Hall, Multipurpose Hall, Food Village, NASU, Sports Centre, Medical Centre, libraries, gates, hostels, administrative facilities, academic buildings, recreation areas, fields, and standalone food/snack hubs.

An outdoor place may have:

- name;
- common name;
- optional short description;
- place type;
- one or more categories;
- aliases/codes;
- representative map point;
- one or more entrances;
- one primary entrance;
- parent school/organizational context where useful;
- active/inactive state;
- verification state;
- internal places.

### 3.2 Internal Place

An internal place belongs to an outdoor parent place.

Examples include lecture halls, event halls, classrooms, laboratories, HOD offices, departmental offices, staff offices, internal food spots, meeting rooms, auditoriums, studios, and other named rooms/facilities.

Internal places normally do **not** need their own outdoor GPS coordinate.

An internal place may have:

- name;
- internal-place type;
- parent outdoor place;
- floor;
- optional room number/code;
- optional department;
- optional wing/section;
- optional short direction note;
- aliases;
- optional associated entrance.

---

## 4. Place Types and Categories

The system should not force all places into `Building`.

### 4.1 Place Type

Suggested initial set:

- Building
- Facility
- Campus Area
- Gate
- Field
- Sports Facility
- Food Hub
- Medical Facility
- Library
- Administrative Facility
- Academic Facility
- Recreation Area
- Hostel
- Other

The implementation may consolidate or refine these labels during Phase 4 planning, but it must preserve the principle that places are not all buildings.

### 4.2 Categories

A place may have one or more functional categories.

Suggested categories include:

- Academic
- Administration
- Classrooms
- Halls & Events
- Food & Snacks
- Sports & Recreation
- Medical
- Library & Study
- Engineering
- Science
- Arts & Design
- Business & Management
- Student Services
- Security
- Accommodation
- Transport / Gate
- Other

A place may legitimately have multiple categories.

Example:

**College Hall**
- Type: Building
- Categories: Academic, Halls & Events

---

## 5. Representative Point vs Entrance

A place's representative point and routing entrance are separate concepts.

### 5.1 Representative Point

The representative point answers:

> Where is this place on the campus map?

The editor may capture it using:

- **Use current location**
- **Pick on map**

During field work, the editor may stand at the building front/entrance and use that position as the initial representative point.

### 5.2 Entrance

The entrance answers:

> Where should navigation bring the user?

A place may have multiple entrances.

Each entrance should support:

- custom name;
- suggested entrance type;
- coordinate;
- optional parent internal place;
- primary/non-primary status;
- active/inactive status.

Suggested entrance type dropdown:

- Main Entrance
- Building Entrance
- Hall Entrance
- Back Entrance
- Side Entrance
- Other

The dropdown is only a convenience. Editors must also be able to type a custom entrance name.

### 5.3 Initial Field Capture

When an editor is physically standing at the front/entrance of a place, YCT Map should allow:

> **Use current location for place + primary entrance**

This may initially create the representative point and primary entrance at the same coordinate.

They must remain independently editable later.

---

## 6. Multiple Entrances

Multiple entrances are required.

An entrance may serve:

- the whole outdoor place; or
- a specific internal destination such as an event hall.

One entrance should be marked as the default/primary arrival point for the parent outdoor place.

If an internal place has its own associated entrance, routing to that internal place should use that entrance.

Otherwise, routing should fall back to the parent outdoor place's primary entrance.

---

## 7. Routing to Internal Places

YCT Map V1 does not require indoor route geometry.

Example search:

> Yusuf Grillo Hall

Expected behavior:

1. Search finds `Yusuf Grillo Hall`.
2. Result explains that it is inside `Arts Complex`.
3. Route goes to the hall-specific entrance if one has been assigned; otherwise Arts Complex primary entrance.
4. Internal guidance may show floor, room/hall name, optional wing/section, and optional short direction note.

This is sufficient for V1.

---

## 8. Floors

Buildings may contain many floors, including tall buildings.

Do not hardcode a small maximum.

The editor must support Ground Floor, 1st Floor, 2nd Floor, 3rd Floor, and so on, including 7th Floor and beyond where necessary.

A flexible numeric floor index plus human-readable label is preferred.

The model should be able to support basement levels later if needed.

---

## 9. Internal Place Types

Suggested initial internal-place types:

- Classroom
- Lecture Hall
- Event Hall
- Laboratory
- Office
- Department
- HOD Office
- Staff Office
- Studio
- Internal Food Spot
- Meeting Room
- Other

These should remain extensible without introducing separate Django models for each type.

---

## 10. Codes, Abbreviations, and Aliases

Codes are useful, but not fundamental identity.

A place has a manually entered real/display name.

Codes, abbreviations, common names, and informal names should be stored as searchable aliases.

Example:

**Science and Technology Building**
- Alias: NASB
- Alias: Science Complex
- Alias: Science & Technology Building

A code changing later must not change the underlying place identity.

Editors should be able to add multiple aliases manually.

Search should match official names, common names, abbreviations, examination codes, alternate spellings, and known nicknames.

---

## 11. Initial Known YABATECH Aliases / Exam Venue References

**Data classification: OWNER-SUPPLIED STARTING REFERENCE DATA — NOT FIELD VERIFIED**

The following list is user-supplied campus knowledge and should be treated as a starting reference, not a final authoritative field-verified dataset:

- **ETF** — Education Trust Fund Building
- **NB** — New Building
- **NASB** — Science and Technology Building / Science Complex
- **ADP ART 01** — Art and Design Building
- **SLS 01, 02** — School of Liberal Studies
- **ENVS** — Old Environmental Studies Building
- **SB** — Secretarial Studies Building / OTM
- **NESB** — New Environmental Studies Building
- **CE** — Civil Engineering Building
- **NSB** — New Science Building
- **MELB** — Engineering Building
- **C5** — Oldest Lecture Theatre
- **PTT 201, 204** — Polymer and Textile Technology Building
- **MB01, 02** — Hospitality Management Building
- **MPGF** — Multipurpose Building
- **MPT** — Multipurpose Theatre / Hall
- **SMBS OLD** — Old School of Management and Business Studies
- **NEW SMBS / OKUFI** — New School of Management and Business Studies

These values should be entered manually into the real dataset during Phase 5 and verified during field mapping.

Do not encode them as hardcoded application logic.

---

## 12. Food and Small Places

YCT Map does not need to map every individual kiosk.

The useful destinations are the stable places students actually ask for.

Examples include Food Village, NASU, Pepsi on the ground floor of Alumni Building, and other established food/snack hubs.

`Pepsi` can be represented as an internal place under Alumni Building.

---

## 13. Building / Place Directory

Outdoor place cards should support a `Places inside` section.

Example:

**SCIENCE COMPLEX**
- Computer Science Department
- Computer Science HOD Office
- Microbiology Department
- Laboratories
- Classrooms
- Other named facilities

Selecting an internal place should show its parent place and floor.

---

## 14. Editor Authentication

Editor authentication must use Django's authentication system.

Do not use:

- hardcoded credentials;
- source-code passwords;
- Supabase Auth as a separate authentication layer;
- student accounts for editor access.

Initial roles:

### Administrator

Can create/manage editor accounts, perform all editor operations, and manage permissions.

### Editor

Can manage campus places, aliases, entrances, internal places, floors, paths when Phase 4 path tooling arrives, contributions as authorized, and verification/mapping tools.

Django Groups/Permissions should be used where appropriate.

Initial editor users are the owner and project team.

---

## 15. Field Mapping Workflow

The editor workflow must match the owner's intended real campus mapping process.

### 15.1 Overall Phase 5 workflow

1. Map/review campus pathways first.
2. Move to a physical building/place.
3. Stand at its front or primary entrance.
4. Create/select the outdoor place.
5. Capture current location for place + primary entrance.
6. Enter place details.
7. Enter the building.
8. Populate internal information floor by floor.
9. Finish the building.
10. Move to the next place.

### 15.2 Outdoor capture workflow

Suggested UI:

**Add Place**

- Name
- Type
- Categories
- School/context
- Aliases/codes
- Representative location:
  - Use current location
  - Pick on map
- Primary entrance:
  - Use same current location
  - Capture separately
  - Pick on map
- Save & enter building
- Save & finish

### 15.3 Current-location capture

When current location is used, show:

- accepted GPS position;
- accuracy;
- clear warning if accuracy is poor;
- manual adjustment option.

The editor should never need to type raw latitude/longitude as the ordinary workflow.

---

## 16. Floor-by-Floor Population Workflow

Inside a building, the editor should be able to rapidly add many internal places without repeatedly re-entering the same parent/floor.

Suggested flow:

**Science Complex**
Current Floor: Ground Floor

[ + Add place on this floor ]

After saving an internal place:

[ + Add another place ]

The system retains parent building, current floor, and optionally current department/context when useful.

When the editor has finished the floor:

[ Finish Floor ]

Then:

[ + Add Another Floor ]
[ Finish Building ]

This workflow is a Phase 4 requirement.

---

## 17. Manual Placement

Manual placement must remain available everywhere current-location capture exists.

Editors may click/tap the map, place a marker, drag/adjust it, and save.

Manual placement is especially important when GPS accuracy is poor, the place is inaccessible, the editor is correcting an existing coordinate, or an entrance can be seen accurately on the map.

---

## 18. Marker / Display Strategy

The dataset may contain many places without showing every place as a permanent marker.

At campus overview, prefer major outdoor destinations.

At closer zoom or through search, additional smaller outdoor places may appear.

Internal places usually do not need persistent map markers. They should remain searchable and available through the parent place's `Places inside` directory.

Rule:

> Outdoor routable place = may have a map marker.
> Internal place = searchable/listed under parent, usually no permanent outdoor marker.

---

## 19. Schools and Organizational Context

YABATECH contains multiple schools.

A place may optionally belong to a school or organizational context.

Example:

**Science Complex**
- School: School of Technology

Internal departments/offices may belong to relevant departments while still sharing the same physical building.

Do not assume that classroom codes encode floor information. Floor should be explicitly stored.

---

## 20. Verification

The following concepts must remain distinct:

- `UNVERIFIED`
- editor-reviewed/corrected
- `FIELD_VERIFIED`

A place captured by an editor is not automatically field-verified unless the Phase 4 verification workflow explicitly records that status.

An approved anonymous contribution is also not field verification.

OSM-derived routing remains `UNVERIFIED` until reviewed/verified separately.

---

## 21. Path Survey Mode Relationship

Path Survey Mode remains a later Phase 4 feature.

It should eventually allow an editor to start a survey, walk an actual path, record a transient GPS trace, compare it against the current routing network, identify matched/missing/incorrect segments, review confidence, and explicitly approve verification/correction.

This specification does not define the detailed survey algorithm.

---

## 22. Explicit Non-Goals

This specification does not require:

- indoor route geometry;
- room-by-room turn-by-turn navigation;
- mapping every kiosk;
- student accounts;
- native mobile app;
- automatic OSM write-back;
- public direct map editing;
- city routing;
- AR navigation;
- photorealistic 3D.

---

## 23. Phase 4 Implementation Priorities

Recommended sequence:

1. Editor authentication and permissions
2. Real campus place model
3. Place types/categories
4. Aliases/codes
5. Entrance model and primary entrance
6. Internal places and floors
7. Building/place directory
8. Current-location/manual placement tools
9. Efficient floor-by-floor editor workflow
10. Contribution review/editor resolution
11. Path editing
12. Verification tooling
13. Path Survey Mode

Exact sprint boundaries should be decided during Phase 4 planning.

---

## 24. Phase 5 Data-Population Strategy

Phase 5 should not begin by randomly placing buildings.

Preferred real-data workflow:

1. establish/review the pathway network;
2. attach entrances to paths;
3. visit places physically;
4. capture outdoor locations;
5. capture primary/additional entrances;
6. populate internal places floor-by-floor;
7. add aliases/exam codes;
8. verify search behavior;
9. conduct field-route testing;
10. correct geometry/data;
11. perform physical-device navigation verification;
12. prepare launch dataset.

---

## 25. Change Control

This document is the approved design baseline for Phase 4.

If implementation reveals a material conflict, Codex must:

1. stop;
2. explain the conflict;
3. propose alternatives;
4. request owner approval before changing the product model.

Minor reversible implementation details may be decided autonomously under the existing Build Control Protocol.

Do not silently simplify this specification back into a building-only map.
