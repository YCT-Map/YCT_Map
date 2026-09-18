# Build Pipeline — YCT Map

This is the **authoritative description of the approved YCT Map V1 build sequence**.

There is no other authoritative pipeline document. Do not create competing pipeline files.

---

## Pipeline Status Summary

```
Phase 1 — Foundation & Map Experience          ACCEPTED
Phase 2 — Routing & Navigation                 IN PROGRESS
Phase 3 — Live Navigation & Core Product       NOT STARTED
Phase 4 — Editor & Mapping Tools               NOT STARTED
Phase 5 — Real YabaTech Data, Verification & Launch   NOT STARTED

Current:            PHASE 2 — SPRINT 002 OWNER ACCEPTED
Next expected:      Phase 2 Sprint 003 discussion / authorization
```

Status values in use: `NOT STARTED` `IN PROGRESS` `BLOCKED` `COMPLETE` `ACCEPTED`

Do not mark a phase `ACCEPTED` without explicit owner approval.

---

## Pipeline Principle

The software must be built and validated primarily with **clearly labelled demonstration data** before serious YabaTech field-data population begins.

Real campus information collection, physical population, and field verification belong in **Phase 5** — intentionally last.

Before spending significant effort collecting real campus information, the team must first prove that:

- map interaction works;
- search works;
- routing works;
- distance calculation works;
- live navigation works;
- contributions work;
- editor tools work.

---

## Sprint Structure Inside Each Phase

Each phase may contain multiple sprints. A sprint record must include:

- Sprint ID and Phase
- Objective
- Approved scope
- Starting state
- Expected deliverable
- Acceptance test
- Tests / checks run
- Evidence captured
- Ending state
- Next recommended sprint

The exact number of sprints varies by phase. Do not force phases to contain equal numbers of sprints.

---

## Standard Evidence Process

Every meaningful sprint follows the same documentation process.

### After every accepted sprint

**1. Capture two screenshots**

| Screenshot | Purpose |
|------------|---------|
| `P{phase}-S{sprint}-A-{description}.png` | Main result — most important visible outcome |
| `P{phase}-S{sprint}-B-{description}.png` | Supporting result — mobile view, route detail, editor screen, test output, etc. |

Examples: `P1-S1-A-first-map.png`, `P2-S2-A-route-result.png`, `P3-S1-B-rerouting.png`

**2. Sprint record** (concise, factual)

```
Phase:
Sprint:
Objective:
What was built:
What was tested:
Problem encountered:
How it was resolved:
Result:
Next step:
```

Technical detail lives in `SPRINT_LOG.md`. The sprint record above is the owner-facing summary.

**3. Owner handoff**

After each accepted milestone, the owner sends the two screenshots to the project documentation assistant for parallel record keeping.

Codex cannot perform this external handoff. Codex should remind the owner that evidence must be captured before moving forward.

---

## Phase-End Evidence

At the end of every major phase:

- Capture two final phase screenshots.
- Capture one short screen recording where useful (approximately 15–60 seconds).
- Produce or update the student-friendly phase summary.
- Run phase acceptance checks.
- Receive explicit owner acceptance before recording `ACCEPTED`.

Recordings are especially useful for: map interactions, routing, live movement, rerouting, editor mapping, contribution moderation.

---

## Phase Acceptance Rule

A phase is not complete merely because implementation exists.

Before marking a phase `COMPLETE` or `ACCEPTED`:

- [ ] Relevant tests pass
- [ ] All acceptance criteria are met
- [ ] Owner has manually verified the milestone
- [ ] Required evidence (screenshots, recording) is captured
- [ ] `CURRENT_STATE.md` is updated
- [ ] `SPRINT_LOG.md` entry is complete
- [ ] Known issues are recorded in `KNOWN_ISSUES.md`
- [ ] Next phase is clearly identified

Record: `PHASE X ACCEPTED` only after all items above are satisfied.

Do not automatically begin the next phase.

---

---

## Phase 1 — Foundation & Map Experience

**Status: ACCEPTED — Sprint 002 owner accepted with one documented cosmetic carryover**

### Primary Goal

Make YCT Map visibly exist as a usable interactive product.

By the end of Phase 1, a user should be able to open YCT Map locally, see the YabaTech map area, search demonstration locations and inspect location information.

### Scope

- Project / application foundation
- Basic local development environment
- Core frontend / backend structure
- Interactive map displayed successfully
- Map initially focused on the YabaTech campus area
- Mobile-first, map-first interface
- Agreed visual direction applied (green, white, grey, yellow — restrained)
- Demonstration location dataset (clearly labelled DEMO)
- Search by name and category
- Demo location categories
- Location selection
- Location cards / detail panels
- Map focus and zoom behaviour when a destination is selected
- Responsive desktop behaviour
- Foundational tests and type-checks
- Project-state documentation updated

### Demo Data Rule

Phase 1 uses clearly labelled demonstration data.

Demo records must never pretend to be verified real YabaTech information.

Do not invent real campus coordinates and mark them trustworthy.

Phase 1 demonstration locations are explicitly synthetic, use the `DEMO` verification/data state, and may be placed within the initial viewport solely to demonstrate product behaviour. They must remain replaceable or removable without changing the production data model.

### Initial Map Foundation

- Use OpenStreetMap way `671850885` as the geographic source for the initial YabaTech viewport.
- Approximate OSM-derived centre: latitude `6.51857`, longitude `3.37424`.
- MapLibre centre ordering: `[3.37424, 6.51857]`.
- Use OpenFreeMap's official Liberty style: `https://tiles.openfreemap.org/styles/liberty`.
- These viewport values do not verify or authorize any individual real campus location.

### Phase 1 User Milestone

A user can:

1. Open YCT Map
2. See the campus map
3. Search for a demonstration location
4. Select it
5. See the map focus on it
6. View useful location details

### Phase 1 Non-Goals

Do not build during Phase 1:

- Real campus population or field verification
- Full routing or path calculation
- Live GPS navigation or rerouting
- Full editor mapping tools
- Public contribution moderation
- Detailed 3D work

### Phase 1 Exit Criteria

- [x] Map loads reliably
- [x] Demonstration locations display correctly
- [x] Search works and returns relevant results
- [x] Location selection works
- [x] Location detail UI works
- [x] Mobile layout is usable
- [x] Desktop layout is acceptable
- [x] Relevant tests and type-checks pass
- [x] Owner personally verifies the main user flow
- [x] Two screenshots captured
- [x] Sprint / phase evidence captured in `SPRINT_LOG.md`

---

## Phase 2 — Routing & Navigation

**Status: IN PROGRESS — Sprint 002 OWNER ACCEPTED; Sprint 003 next**
**Depends on:** Phase 1 ACCEPTED

### Primary Goal

Transform YCT Map from a searchable campus map into a walking-navigation system.

By the end of Phase 2, a user should be able to choose a starting location and destination and receive a calculated walking route.

### Scope

- Demonstration walkable path network (clearly labelled DEMO)
- Route representation in the data model
- Routing graph built from path geometry
- Route calculation algorithm
- Route visualization drawn on the map
- Automatic route-distance calculation from geographic geometry
- Estimated walking time display
- Origin selection (search or map tap)
- Destination selection
- Manual starting-point selection
- Basic written or structured route guidance where appropriate
- Route error and empty states handled
- Route-related tests

### Critical Rule

Route distance **must** be calculated from geographic path geometry.

Distances must **not** be manually entered between location pairs.

Building shape does not determine route distance.

Routing is based on walkable path connections and destination arrival points.

### Phase 2 User Milestone

A user can:

1. Choose a demonstration starting point
2. Choose a demonstration destination
3. Request directions
4. See the route drawn on the map
5. See the calculated walking distance
6. See the estimated walking time

### Phase 2 Non-Goals

Do not begin during Phase 2:

- Real campus mapping or data collection
- Full editor location-management tools
- Production campus data population
- Live GPS rerouting (Phase 3)
- Large-scale contribution workflows (Phase 3)
- Detailed 3D modelling

### Phase 2 Exit Criteria

- [ ] Routing works across the demonstration path network
- [ ] Route distances are calculated automatically from geometry
- [ ] Walking ETA is displayed
- [ ] Invalid and unreachable route cases are handled gracefully
- [ ] Route rendering works correctly on mobile
- [ ] Relevant tests pass
- [ ] Owner personally verifies representative routes
- [ ] Two screenshots captured
- [ ] Sprint / phase evidence captured in `SPRINT_LOG.md`

---

## Phase 3 — Live Navigation & Core Product Systems

**Status: NOT STARTED**
**Depends on:** Phase 2 ACCEPTED

### Primary Goal

Make YCT Map behave like a real navigation product while keeping it lightweight.

### Scope

- Browser / device location permission request
- Current-location display on the map
- Live position updates as the user moves
- Moving user indicator
- Route progress behaviour
- GPS accuracy handling
- Off-route tolerance threshold
- Controlled rerouting when user materially leaves the route
- Updated remaining distance where appropriate
- Relevant navigation states (en route, arrived, off-route, rerouting)
- Student contribution submission flow
- Public contribution submission without a student account
- Initial contribution moderation workflow (backend + editor review queue)
- Mobile performance refinement
- Navigation and contribution tests

### Normal User Rule

Students, staff and visitors do **not** require regular accounts.

Location permission is optional.

Users who do not enable location services must still be able to choose a manual starting point and navigate using it.

### Rerouting Rule

Do not reroute because of every small GPS fluctuation.

Use sensible position tolerance and require evidence of a material departure before triggering rerouting.

GPS noise must not cause unnecessary rerouting.

### Public Contribution Rule

Students may submit campus information without an account.

They must **not** directly edit verified public map data.

All submissions must enter moderation before appearing in the public dataset.

### Phase 3 User Milestone

A student can:

1. Enable location and see their position on the map
2. Begin navigation to a destination
3. See their position update while moving
4. Be rerouted when materially off-route
5. Submit missing or corrected campus information without an account

### Phase 3 Non-Goals

Do not during Phase 3:

- Perform full real YabaTech dataset population (Phase 5)
- Spend significant effort field-mapping real campus information
- Prioritize complex 3D work over navigation reliability

### Phase 3 Exit Criteria

- [ ] Live location works on supported browser/device conditions
- [ ] Position updates correctly while moving
- [ ] GPS noise is handled without spurious rerouting
- [ ] Rerouting behaviour triggers correctly on real departure
- [ ] Contribution submission works without an account
- [ ] Moderation basics work (editor can see and act on submissions)
- [ ] Mobile experience remains performant
- [ ] Tests and checks pass
- [ ] Owner verifies the core navigation and contribution flows
- [ ] Two screenshots + one short recording captured
- [ ] Sprint / phase evidence captured in `SPRINT_LOG.md`

---

## Phase 4 — Editor & Mapping Tools

**Status: NOT STARTED**
**Depends on:** Phase 3 ACCEPTED

### Primary Goal

Make YCT Map maintainable by the project team without requiring source-code edits.

Phase 4 builds the tools the team will use during the real campus population phase (Phase 5).

### Scope

- Editor / admin authentication
- Location add / edit / delete
- Category management
- Alias management
- Verification state management (DEMO / UNVERIFIED / FIELD_VERIFIED)
- Main entrance / arrival-point setting via map interface
- Internal location management (departments, offices, classrooms, lecture rooms)
- Parent building relationships
- Floor information
- Map-based location selection (click/tap to set coordinates)
- Current-location selection where useful
- Missing-location representation
- Irregular building geometry support where needed (polygon points, not assumed rectangular)
- Walkable path add / edit / delete
- Editor-only Path Survey Mode foundation: GPS breadcrumb capture, map matching, confidence handling and explicit review; one raw trace must never create `FIELD_VERIFIED` status
- Contribution review queue:
  - Approve
  - Edit and approve
  - Merge duplicate
  - Reject
  - Flag / request correction
- Review history / audit trail where appropriate
- Editor-focused tests

### Editor Interface Rule

Editors should not need to interact with raw geographic coordinate numbers for normal workflows.

Prefer:

- Click the map to set a location
- Use current GPS position
- Select parent building from a list
- Choose category from a list
- Enter name and aliases
- Choose verification status

### Irregular Building Rule

Do not assume buildings are rectangular.

Irregular building geometry uses polygon points.

However, exact building outlines are not mandatory for navigation. A correct destination point and primary entrance are more important than a perfect outline.

### Phase 4 User Milestone

An authorized editor can populate and maintain YCT Map without modifying application source code.

### Phase 4 Non-Goal

Full real campus population still belongs to Phase 5. Demo data remains in use during Phase 4 development and testing.

### Phase 4 Exit Criteria

- [ ] Editor authentication works
- [ ] Location CRUD works as approved
- [ ] Internal locations can be attached to parent buildings with floor information
- [ ] Entrances can be set via map interface
- [ ] Paths can be added, edited and deleted
- [ ] Verification state can be set (and requires deliberate action for FIELD_VERIFIED)
- [ ] Contribution review workflow is complete (all five actions work)
- [ ] Common editor tasks require no code changes
- [ ] Relevant tests pass
- [ ] Owner verifies the complete editor workflow
- [ ] Two screenshots + one recording captured
- [ ] Sprint / phase evidence captured in `SPRINT_LOG.md`

---

## Phase 5 — Real YabaTech Data, Field Verification & Launch

**Status: NOT STARTED**
**Depends on:** Phase 4 ACCEPTED

### Primary Goal

Convert the completed software platform into a verified real-world YabaTech navigation system and launch V1.

This is the phase where serious campus information work occurs.

### Scope

#### Campus Data Population

- Campus inventory and planning
- Replacement / expansion of demonstration data with real records
- Real building and destination names
- Useful search aliases
- Correct categories
- Main entrances / arrival points
- Internal departments, offices, classrooms, lecture rooms with floors
- Food locations, hostels, gates, sports facilities, administrative locations, libraries, medical facilities
- Missing walkable paths represented within YCT Map
- Missing locations added

#### Field Verification

- Use the reviewed Path Survey Mode during campus field work where it reduces manual tracking effort
- Keep unwalked path-network sections identifiable and review missing-path observations before changing trusted data
- Representative route walking on campus
- Correction of inaccessible paths (crossing walls, fences, restricted areas)
- Correction of inaccurate entrances
- Correction of misleading routes
- Full campus dataset review
- Marking records FIELD_VERIFIED only after physical confirmation

#### Launch Preparation

- Mobile polish
- Performance refinement for student devices
- Modest 3D / depth enhancement only if stable and non-blocking
- Final regression testing
- Deployment to production
- Launch validation and smoke tests
- Handover

### Data Collection Principle

Use the least stressful reliable process:

1. Reuse accurate existing map information where available
2. Use team knowledge for known locations
3. Populate known locations through Editor Mode
4. Identify uncertainties explicitly
5. Visit only uncertain or missing places in person
6. Physically walk-test representative routes between major buildings
7. Correct verified problems found during walk-testing

Do not attempt to physically visit every location by default.

### FIELD VERIFIED Definition

A location or path is FIELD VERIFIED only when:

- The destination physically exists at the recorded position
- The name is correct
- The entrance / arrival point is useful (physically accessible)
- The walkable route actually exists on the ground
- The route does not pass through walls, fences or inaccessible areas
- Relevant internal information (floor, department, office) is accurate
- Confirmed by a trusted team member with physical access

### Demo Data Separation

At production launch, demo records must be clearly distinguished from real campus data.

Demo data must not appear as FIELD_VERIFIED in any production user-facing context.

### Phase 5 User Milestone

A real YabaTech student can open the deployed application and use YCT Map to find and navigate important parts of the campus.

### Phase 5 Exit Criteria

- [ ] Important campus areas are populated with real data
- [ ] Production campus data is clearly distinguished from demo data in the database
- [ ] Representative campus routes are field-tested
- [ ] Major routing errors are corrected
- [ ] Editor workflow is operational in production
- [ ] Student contribution workflow is operational in production
- [ ] Mobile performance is acceptable on ordinary student smartphones
- [ ] Final regression tests pass
- [ ] Application is deployed to production
- [ ] Production smoke tests pass
- [ ] Owner accepts final V1
- [ ] Final evidence is captured (screenshots + recording)
- [ ] Sprint / phase evidence captured in `SPRINT_LOG.md`
- [ ] `CURRENT_STATE.md` updated to reflect launch
- [ ] `CHANGELOG.md` updated with V1 milestone
- [ ] Project handover complete

---

## V1 Feature Boundary

### V1 Includes

- Mobile-first web experience
- YabaTech-focused map (no city-wide navigation)
- No regular student accounts required
- Search by name, alias, category
- Physical locations (buildings, schools, gates, hostels, libraries, sports areas, food, medical, admin, other)
- Internal locations (departments, offices, classrooms, lecture rooms) with parent building and floor
- One primary arrival point per location
- Manual starting-point selection
- Optional current-location (GPS)
- Route visualization on map
- Route distance (from geometry)
- Walking ETA
- Basic written / step-by-step route guidance
- Live position movement during navigation
- Controlled rerouting on material departure
- Student contributions without an account
- Contribution moderation
- Editor tools (add, edit, verify, manage paths, review contributions)
- Field verification workflow
- Missing-location and missing-path support
- Lightweight visual depth / 3D only where appropriate and stable

### V1 Does Not Require

- Navigation outside YabaTech campus
- Native Android / iOS apps
- Student user accounts
- Detailed indoor floor-plan navigation
- Multiple entrances per building
- Location photographs
- Offline maps
- Voice navigation
- Augmented reality
- Photorealistic 3D
- Ratings or reviews
- Comments or social features

Do not move V2 ideas into V1 because they are technically interesting.

---

## Relationship to Other Documents

| Document | Role |
|----------|------|
| `BUILD_PIPELINE.md` (this file) | Phases, goals, deliverables, exit criteria, sequencing |
| `SPRINT_LOG.md` | Actual work history, sprint implementation, problems, decisions |
| `CURRENT_STATE.md` | Current position within this pipeline — updated every sprint |
| `DECISIONS.md` | Material decisions that shaped the pipeline |
| `KNOWN_ISSUES.md` | Issues discovered during sprints |
| `BACKLOG.md` | Ideas not in the current sprint |

Do not turn this file into a chronological sprint diary. That belongs in `SPRINT_LOG.md`.

---

## Conflict Note

The previous version of this document described a 10-phase sequence (Phase 0 through Phase 10). That structure has been superseded and replaced by this authoritative 5-phase pipeline. If any other document still references the old phase numbering, it should be updated to match this document.
