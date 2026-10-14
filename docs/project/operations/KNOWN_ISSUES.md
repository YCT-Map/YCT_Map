# Known Issues — YCT Map

This document records known bugs, limitations, technical debt and temporary compromises.

Updated as issues are discovered. Do not list speculative concerns as confirmed bugs.

---

## Current Phase

PHASES 1, 2 and 3 are OWNER ACCEPTED / COMPLETE.

## Active Limitations

- The current 49-node/54-segment local graph and eligible retained campus records are owner-attested and `FIELD_VERIFIED`. Verification does not make the graph denser: 41 nodes form the destination-reachable component, while one six-node component and two isolated nodes remain disconnected. Some valid in-campus live positions are therefore separated from a destination-reachable mapped segment by an unmapped gap.
- A campus-scoped sparse-graph match may therefore return `APPROACH_REQUIRED`. Its dashed line is an orientation-only guide, not a claimed walkway, and its gap is excluded from route distance and ETA.
- The closeout orientation correction has deterministic cardinal and landscape coverage but still requires a physical Samsung/Edge N/E/S/W walking retest.
- Live-origin routing, progress, dynamic ETA, off-route detection and controlled rerouting retain deterministic regression coverage. Destination-aware matching prevents an origin from attaching to graph geometry that cannot reach the selected destination, but physical behavior still depends on browser/device sensor quality and available graph coverage.
- Rerouting is campus-graph only. It does not provide city routing or complete outside-campus recovery.
- ETA uses a filtered personal pace only after sufficient reliable movement; otherwise it intentionally falls back to approximately `1.35 m/s`.
- Phase 3 Sprint 004 moderation uses Django admin. Phase 4 Sprint 003 adds explicit, repeatable resolution records, but detailed owner QA of that custom resolution workflow is deferred.
- Anonymous throttling uses process-local cache in local development. A shared production cache must be selected before multi-instance deployment.
- Live public records are distinct from test-only DEMO fixtures. The current eligible retained baseline is owner-attested and promoted locally to `FIELD_VERIFIED`; new, imported or materially edited records retain the normal `UNVERIFIED` default/demotion rules, and DEMO records remain DEMO.
- Approved contributions require explicit authenticated editor action; approval and resolution intentionally do not automatically publish, alter map data or grant `FIELD_VERIFIED`.
- Sprint 002 implementation remains present and regression-tested, but its dedicated owner acceptance is still explicitly deferred.
- Path Survey evidence, revision-bound matching, cumulative one-way promotion and explicit verification transitions are implemented. Review-only `SurveySegmentMatch` decisions now store the latest actor and timestamp; pre-migration decisions correctly remain labelled as historical reviews without fabricated audit metadata.
- Browser geolocation is an uncertainty-bearing estimate, not survey-grade positioning. The local reliability correction rejects cached/old callbacks, requires fresh multi-sample convergence and hard-resets long-idle evidence, but it cannot improve device hardware, radio visibility, OS sensor fusion or browser quality. Physical Samsung/Edge cold-start, long-resume, weak-signal, stationary and walking validation remains required.

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
Impact:       A precise in-campus live position can be separated from the sparse explicit graph. The former nearest-segment flow could repeatedly reject it, attach to a component that could not reach the selected destination, or appear to do nothing while retrying.
Workaround:   Use a static mapped start in the currently deployed build if live route setup cannot connect safely.
Resolution:   Match only against graph segments that can reach the selected destination. Return explicit `ON_NETWORK`, `APPROACH_REQUIRED` or `ARRIVAL_CANDIDATE` states; constrain the wider sparse-campus allowance to the approved campus boundary; render any gap as an orientation-only guide excluded from route distance/ETA; and surface bounded setup/recovery errors. Arrival requires repeated evidence.
Status:       RESOLVED LOCALLY; physical Samsung/Edge owner retest pending.
```

### KI-005

```
ID:           KI-005
Severity:     HIGH
Type:         BUG / LOCATION FRESHNESS
Impact:       A cached or lone accurate-looking callback could publish after startup, and a long-idle reacquisition could reuse an earlier session's stabilizer evidence. The map could therefore appear confidently positioned at an old or insufficiently confirmed coordinate.
Workaround:   In the deployed baseline, stop and restart location outdoors with Precise Location enabled; do not begin live routing until the marker visibly agrees with the user's position.
Resolution:   Disallow cached initial fixes, reject browser callbacks older than five seconds, require fresh multi-sample convergence, never promote one fix at the acquisition deadline, hard-reset long-idle/manual reacquisition evidence and gate routing on explicit confirmation.
Status:       RESOLVED LOCALLY; physical Samsung/Edge owner retest pending. Not committed, pushed or deployed.
```

---

> Update this document when issues are discovered during sprints or testing.
> Link issues to relevant sprint log entries where applicable.
