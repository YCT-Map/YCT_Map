# Known Issues — YCT Map

This document records known bugs, limitations, technical debt and temporary compromises.

Updated as issues are discovered. Do not list speculative concerns as confirmed bugs.

---

## Current Phase

PHASES 1 AND 2 and Phase 3 Sprint 001 are OWNER ACCEPTED.

## Active Limitations

- The 47-node/54-segment OSM-derived development network is `UNVERIFIED`; service-road walkability and physical access are not guaranteed.
- Exact entrances and exits are not deeply mapped, and some destination arrival anchors remain approximate.
- Browser live-location display is implemented, but physical-phone GPS is not yet verified because no approved HTTPS test origin exists.
- Live location is not yet a route origin; live route progress, rerouting, Path Survey Mode and the complete editor mapping interface are not implemented.
- ETA uses the approximate `1.35 m/s` fallback rather than measured live walking speed.
- When a worse incoming location sample is rejected, the previous better marker is correctly retained but the UI does not yet explicitly explain that decision.

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
