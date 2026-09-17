# Risks — YCT Map

This document records material risks to the project.

---

## Risk Format

```
ID:           RISK-XXX
Risk:         Description of the risk
Likelihood:   HIGH | MEDIUM | LOW
Impact:       HIGH | MEDIUM | LOW
Mitigation:   Current or planned mitigation
Trigger:      What event would require action
```

---

## Active Risks

### RISK-001

```
ID:           RISK-001
Risk:         Campus data quality — real YabaTech locations, paths and entrances are unknown until field visits occur.
Likelihood:   HIGH (confirmed — no verified data exists yet)
Impact:       HIGH — users will get incorrect navigation if real data is inaccurate
Mitigation:   Build with demo data first (DEC-005). Define a field verification workflow. Do not mark data FIELD_VERIFIED without physical confirmation.
Trigger:      Any attempt to deploy with unverified campus data as production data.
```

---

### RISK-002 — RESOLVED 2026-09-17

```
ID:           RISK-002
Risk:         Technology stack decisions were initially unresolved and blocked implementation planning.
Likelihood:   RESOLVED
Impact:       NONE CURRENT — DEC-T01 through DEC-T14 are accepted.
Mitigation:   Foundational stack, hosting, map service, viewport, demo-data and routing assumptions are recorded in DECISIONS.md.
Trigger:      Reopen only if an approved decision becomes infeasible or requires material replacement.
```

---

### RISK-003

```
ID:           RISK-003
Risk:         Performance on low-end student devices — map tile loading, routing and search may be slow.
Likelihood:   MEDIUM
Impact:       HIGH — if the app is too slow, students will not use it
Mitigation:   Lightweight design principle (approved). Tile provider choice affects this. Performance testing on real devices required before launch.
Trigger:      Performance review in Phase 5 (launch preparation).
```

---

### RISK-004

```
ID:           RISK-004
Risk:         GPS accuracy on campus — building density and materials may degrade GPS accuracy.
Likelihood:   MEDIUM
Impact:       MEDIUM — live navigation may be less accurate than expected
Mitigation:   GPS noise filtering (approved requirement). Rerouting threshold must be tuned against real campus conditions.
Trigger:      Field testing with GPS.
```

---

### RISK-005

```
ID:           RISK-005
Risk:         Contribution spam / abuse — open contribution system (no account required) may attract low-quality or malicious submissions.
Likelihood:   MEDIUM (post-launch, after visibility)
Impact:       MEDIUM — editor workload increases; data quality risk if moderation is slow
Mitigation:   Moderation queue (all contributions reviewed before publish), strict server-side validation and IP-based rate limiting. Add CAPTCHA only if evidence demonstrates a need (DEC-T10).
Trigger:      Noticeable spam volume in contribution queue.
```

---

### RISK-006

```
ID:           RISK-006
Risk:         Map tile provider costs or availability — if the chosen provider changes pricing or availability, the map may break or become expensive.
Likelihood:   LOW (but provider-dependent)
Impact:       HIGH — if base tiles fail, the entire application fails
Mitigation:   OpenFreeMap Liberty is approved initially. Keep the provider replaceable and keep YCT Map campus data independent from the base-map service.
Trigger:      Provider price change or outage.
```
