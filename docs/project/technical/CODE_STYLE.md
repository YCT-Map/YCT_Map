# Code Style — YCT Map

## Status

```
Current phase:     PHASE 1 — FOUNDATION & MAP EXPERIENCE
Implementation:    CONVENTIONS ESTABLISHED
```

Code style conventions will be established during the foundation build phase using Python/Django and modular JavaScript idioms.

This document will be updated with repository-specific conventions once the stack is confirmed and code begins to exist.

---

## Confirmed Principles

- Clarity over cleverness. See `docs/project/governance/ENGINEERING_RULES.md` Rule 14.
- Reuse before creating. See Rule 3.
- Keep scope narrow. See Rule 4.
- Prefer explicit over clever. See Rule 14.

---

## API Contract

The approved backend is Django and the approved API direction is REST.

See `docs/project/technical/API_CONTRACT.md`.

---

## Linting and Formatting

Current baseline checks are Django system checks, migration drift checks, Python compilation and Node JavaScript syntax checks. A dedicated formatter/linter may be introduced when justified by repository size; none is required to run the current application.

---

## Naming Conventions

- Python modules and functions use `snake_case`; classes use `PascalCase`.
- Django models use controlled `TextChoices` for project-owned enumerations.
- Public API serialization is explicit; model objects are never serialized wholesale.
- Frontend JavaScript uses small native ES modules with named exports.
- CSS uses component-oriented class names and shared custom-property tokens.

---

> These conventions reflect the accepted Sprint 001 implementation and should evolve deliberately with later accepted work.
