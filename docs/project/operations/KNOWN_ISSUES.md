# Known Issues — YCT Map

This document records known bugs, limitations, technical debt and temporary compromises.

Updated as issues are discovered. Do not list speculative concerns as confirmed bugs.

---

## Current Phase

PHASES 1, 2 and 3 are OWNER ACCEPTED / COMPLETE.

## Active Limitations

- The 47-node/54-segment OSM-derived development network is `UNVERIFIED`; service-road walkability and physical access are not guaranteed.
- Exact entrances and exits are not deeply mapped, and some destination arrival anchors remain approximate.
- Browser live-location display is implemented, but physical-phone GPS is not yet verified because no approved HTTPS test origin exists.
- Live-origin routing, progress and dynamic ETA are verified with simulated localhost traces; physical GPS/navigation remains unverified.
- Stationary and arrival transitions have deterministic automated coverage but were not cleanly completed during owner manual simulation.
- Off-route detection and controlled rerouting are verified with simulated coordinates; physical-device behavior remains unverified. Path Survey Mode is not implemented.
- Rerouting is campus-graph only. It does not provide city routing or complete outside-campus recovery.
- ETA uses a filtered personal pace only after sufficient reliable movement; otherwise it intentionally falls back to approximately `1.35 m/s`.
- Phase 3 Sprint 004 moderation uses Django admin. Phase 4 Sprint 003 adds explicit, repeatable resolution records, but detailed owner QA of that custom resolution workflow is deferred.
- Anonymous throttling uses process-local cache in local development. A shared production cache must be selected before multi-instance deployment.
- Demo destinations remain in use. Place, entrance, floor, internal-place and routing editor foundations exist, but real campus population and field verification have not begun.
- Approved contributions require explicit authenticated editor action; approval and resolution intentionally do not automatically publish, alter map data or grant `FIELD_VERIFIED`.
- Sprint 002 implementation remains present and regression-tested, but its dedicated owner acceptance is still explicitly deferred.
- Existing verification fields are preserved as data, but ordinary Sprint 003 entrance/internal-place forms do not grant `FIELD_VERIFIED`; Sprint 004 must define evidence records and explicit verification transitions.

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

---

> Update this document when issues are discovered during sprints or testing.
> Link issues to relevant sprint log entries where applicable.
