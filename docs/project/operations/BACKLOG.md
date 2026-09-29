# Backlog — YCT Map

Backlog items are worthwhile ideas that are **not required** for the current approved sprint.

Do not implement backlog items without explicit owner approval.

See `docs/project/governance/BACKLOG_RULES.md` for rules.

---

## Backlog Format

```
ID:         BL-XXX
Idea:       Description
Reason:     Why it is worth recording
Priority:   HIGH | MEDIUM | LOW
Dependency: What must exist first
Release:    Possible release (V1.1 / V2 / Later / Unknown)
Status:     OPEN | APPROVED | DEFERRED | REJECTED
```

---

## Open Items

### BL-001

```
ID:         BL-001
Idea:       Location photographs
Reason:     Photos would help users confirm they are at the right destination, especially for unfamiliar buildings.
Priority:   MEDIUM
Dependency: V1 location management, storage infrastructure
Release:    V2
Status:     OPEN
```

---

### BL-002

```
ID:         BL-002
Idea:       Multiple entrances per outdoor place
Reason:     Some buildings have multiple meaningful entrance points. A single entrance may not be optimal for all routes.
Priority:   MEDIUM
Dependency: Phase 4 campus-place foundation
Release:    V1 / Phase 4
Status:     IMPLEMENTED / OWNER ACCEPTED IN PHASE 4 SPRINT 002
```

---

### BL-003

```
ID:         BL-003
Idea:       Optional student accounts
Reason:     Would allow saving favourite locations, navigation history, and personalized experience.
Priority:   LOW
Dependency: V1 complete
Release:    V2
Status:     OPEN
```

---

### BL-004

```
ID:         BL-004
Idea:       Offline map support
Reason:     Students on very limited data or in coverage dead zones could still use the app.
Priority:   LOW
Dependency: Significant architecture work — tile caching, offline routing
Release:    Later
Status:     OPEN
```

---

### BL-005

```
ID:         BL-005
Idea:       Accessibility-optimized routing (step-free, avoiding stairs)
Reason:     Important for students with mobility needs.
Priority:   MEDIUM
Dependency: Accessibility metadata on paths (not in V1)
Release:    V2
Status:     OPEN
```

---

### BL-006

```
ID:         BL-006
Idea:       Voice navigation
Reason:     Useful for users navigating while looking at their surroundings rather than a screen.
Priority:   LOW
Dependency: V1 routing complete; text-to-speech integration
Release:    Later
Status:     OPEN
```

---

### BL-007

```
ID:         BL-007
Idea:       Editor-only Path Survey Mode using browser GPS breadcrumb traces and map matching against YCT Map's walkable-path network.
Reason:     Survey tooling can help the team identify walked, unwalked and potentially missing path sections during later campus verification without treating noisy raw GPS as trusted geometry.
Priority:   HIGH
Dependency: Phase 2 walkable-path network and Phase 4 authenticated editor tooling
Release:    Phase 4 tooling; Phase 5 field use
Status:     APPROVED — NEXT FOR PHASE 4 SPRINT 004 PRE-BUILD REVIEW
```

Required safeguards:

- tolerate GPS noise;
- compare recorded movement with the existing YCT Map path network;
- keep unwalked network sections visually identifiable;
- allow editors to flag an observed missing path;
- never promote one raw GPS trace directly to `FIELD_VERIFIED`;
- require editor review, map matching and confidence rules before survey status changes.
- flag ordinary outdoor path geometry intersecting building footprints for review;
- allow deliberate reviewed exceptions for genuine passages or corridors.

---

### BL-008

```
ID:         BL-008
Idea:       Optional owner-managed landmark priority metadata for semantic-zoom exceptions
Reason:     A small number of genuinely important campus landmarks may later need explicit close-review visibility rules without deriving importance from category names or invented heuristics.
Priority:   LOW
Dependency: A demonstrated product need and owner-defined values
Release:    Later
Status:     DEFERRED
```

No priority values should be inferred automatically from current campus records.

---

### BL-009

```
ID:         BL-009
Idea:       YCT-owned campus geometry enrichment
Reason:     Replace or augment contextual base-map assumptions with field-reviewed campus boundary, building footprints, pedestrian paths, relevant land/areas and landmarks owned by YCT Map.
Priority:   MEDIUM
Dependency: Approved data model and explicit campus field-review workflow
Release:    Later data-enrichment phase
Status:     OPEN
```

OSM/OpenFreeMap geometry remains contextual and `UNVERIFIED` unless it passes the project's explicit field-verification process. This item must preserve provenance and must not silently promote base-map geometry into trusted campus records.

---

> Add items here when they arise during sprints. Do not implement them without approval.
