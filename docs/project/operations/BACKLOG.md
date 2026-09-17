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
Idea:       Multiple entrances per building
Reason:     Some buildings have multiple meaningful entrance points. A single entrance may not be optimal for all routes.
Priority:   MEDIUM
Dependency: V1 routing complete
Release:    V1.1 or V2
Status:     OPEN
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

> Add items here when they arise during sprints. Do not implement them without approval.
