# Known Issues — YCT Map

This document records known bugs, limitations, technical debt and temporary compromises.

Updated as issues are discovered. Do not list speculative concerns as confirmed bugs.

---

## Current Phase

PHASES 1, 2 and 3 are OWNER ACCEPTED / COMPLETE.

## Active Limitations

- The 47-node/54-segment OSM-derived development network is `UNVERIFIED`; service-road walkability and physical access are not guaranteed.
- Exact entrances and exits are not comprehensively field verified; legacy node-only anchors and approximate connectors remain possible.
- The closeout orientation correction has deterministic cardinal and landscape coverage but still requires a physical Samsung/Edge N/E/S/W walking retest.
- Live-origin routing, progress, dynamic ETA, off-route detection and controlled rerouting retain deterministic regression coverage; field accuracy depends on browser/device sensor quality and the unverified graph.
- Rerouting is campus-graph only. It does not provide city routing or complete outside-campus recovery.
- ETA uses a filtered personal pace only after sufficient reliable movement; otherwise it intentionally falls back to approximately `1.35 m/s`.
- Phase 3 Sprint 004 moderation uses Django admin. Phase 4 Sprint 003 adds explicit, repeatable resolution records, but detailed owner QA of that custom resolution workflow is deferred.
- Anonymous throttling uses process-local cache in local development. A shared production cache must be selected before multi-instance deployment.
- Live public records are distinct from test-only DEMO fixtures. Retained legitimate campus and routing records remain `UNVERIFIED` until explicit evidence supports promotion.
- Approved contributions require explicit authenticated editor action; approval and resolution intentionally do not automatically publish, alter map data or grant `FIELD_VERIFIED`.
- Sprint 002 implementation remains present and regression-tested, but its dedicated owner acceptance is still explicitly deferred.
- Path Survey evidence, revision-bound matching, cumulative one-way promotion and explicit verification transitions are implemented. Review-only `SurveySegmentMatch` decisions now store the latest actor and timestamp; pre-migration decisions correctly remain labelled as historical reviews without fabricated audit metadata.
- Browser geolocation is an uncertainty-bearing estimate, not survey-grade positioning. The closeout filter reduces jitter and stale-fix risk but cannot improve device hardware, radio visibility or browser sensor quality; physical Samsung/Edge validation remains required.

---

## Issue Format

```
ID:           KI-XXX
Severity:     CRITICAL | HIGH | MEDIUM | LOW
Type:         BUG | LIMITATION | DEBT | WORKAROUND
Impact:       Who is affected and how
Workaround:   Current workaround if any
Resolution:   Planned fix or UNKNOWN
```

---

## Resolved Issues

### KI-001

```
ID:           KI-001
Severity:     LOW
Type:         BUG / PRESENTATION
Impact:       At close map zoom levels, the polygon-based `YabaTech Campus` text may be placed repeatedly. Campus orientation and data integrity are unaffected.
Workaround:   Use the boundary, surrounding roads and return-to-campus control for orientation.
Resolution:   Replace polygon symbol placement with one deterministic point label as the first Phase 2 Sprint 001 implementation action.
Status:       RESOLVED in Phase 2 Sprint 001; campus geometry and framing were retained.
```

### KI-002

```
ID:           KI-002
Severity:     HIGH
Type:         BUG / NAVIGATION
Impact:       Landscape screen correction could invert the live arrow by 180 degrees relative to physical movement.
Workaround:   Use the live dot or movement context until the corrected asset is deployed and physically retested.
Resolution:   Apply screen orientation once with the correct sign; keep north-up artwork and MapLibre bearing handling independent.
Status:       RESOLVED LOCALLY in the Final Project Closeout Sweep; physical owner retest pending.
```

### KI-003

```
ID:           KI-003
Severity:     HIGH
Type:         BUG / EDITOR NAVIGATION
Impact:       A failed Entrance create POST could expose URLs for an unsaved UUID, leading Edge to request form resubmission and then reach a 404.
Workaround:   None required in the corrected local build.
Resolution:   Use explicit create/edit state, canonical form actions, stable named GET redirects and safe stale-CSRF recovery.
Status:       RESOLVED LOCALLY in the Final Project Closeout Sweep; owner browser retest pending.
```

### KI-004

```
ID:           KI-004
Severity:     HIGH
Type:         BUG / NAVIGATION RECOVERY
Impact:       A precise live position inside Sports Complex can be about 65 m from the explicit routing graph. The safe 40 m match correctly rejects it, but the previous UI repeatedly retried and appeared to do nothing.
Workaround:   Choose Sports Complex as a mapped start in the committed build.
Resolution:   On this specific safe-match failure, offer the existing route from a nearby route-capable place entrance, disclose the unmapped approach and delay live progress/rerouting until the route start is reached.
Status:       RESOLVED LOCALLY; physical Samsung/Edge owner retest pending.
```

---

> Update this document when issues are discovered during sprints or testing.
> Link issues to relevant sprint log entries where applicable.
