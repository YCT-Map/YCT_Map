# AGENTS.md — YCT Map

This is the **primary entry point** for all coding agents (Codex, Claude, Gemini, Cursor, and any future model or tool).

Read this document completely before beginning any work.

---

## What Is This Repository

**YCT Map** is a mobile-first, web-based navigation and campus information platform dedicated to Yaba College of Technology (YabaTech), Lagos, Nigeria.

The map is the primary interface. There is no unnecessary landing page before the map experience.

---

## Before Any Implementation

Read these documents in order:

1. `docs/project/operations/CURRENT_STATE.md` — current phase, branch, active work, blockers
2. `docs/project/product/PROJECT_BRIEF.md` — what the product is
3. `docs/project/product/V1_SCOPE.md` — what is and is not in V1
4. `docs/project/operations/DECISIONS.md` — decisions already made
5. Latest entry in `docs/project/operations/SPRINT_LOG.md`
6. Documentation directly related to the requested task

Then **inspect the actual repository source code**.

Do not implement anything based on documentation alone without inspecting real code.

---

## Documentation Authority Hierarchy

| Level | Source | Authority Over |
|-------|--------|---------------|
| **1 — Governance** | `docs/project/governance/` and this file | How agents and developers must behave |
| **2 — Approved Product Intent** | `docs/project/product/` and `DECISIONS.md` | What YCT Map is supposed to become |
| **3 — Approved Technical Intent** | `docs/project/technical/` | Accepted architecture and technical decisions |
| **4 — Repository Reality** | Source code, migrations, config, tests, deployed behavior | What currently exists |

**When documentation and code conflict:**
1. Identify the conflict.
2. Determine whether the implementation is wrong or the documentation is stale.
3. Report the conflict — do not silently choose.
4. Resolve deliberately.
5. Update the appropriate source afterward.

Never silently change approved product intent to match a hasty implementation.

---

## Critical Rules

### Scope
- Implement only the approved task.
- Do not redesign product decisions recorded in `docs/project/product/` or `DECISIONS.md`.
- Put useful unrelated ideas in `docs/project/operations/BACKLOG.md`.

### Inspection
- Inspect relevant files before editing.
- Understand existing abstractions, trace data flows, identify tests.
- Do not assume architecture from filenames alone.

### Demonstration Data
- Software must be built first using **explicitly labelled demonstration/seed data**.
- Demo data must **never** be represented as verified YabaTech campus information.
- Fake coordinates must not be assigned to real campus names and marked trustworthy.
- Demo records must be removable without damaging the production data model.

### Real YabaTech Facts
- **Never invent, infer, or mark as verified** a real YabaTech location, building outline, entrance, walkable path, floor, or internal destination without trusted project data.
- If required information is unknown: use explicit demo data, mark information unverified, or request owner/team verification.
- Real YabaTech coordinates, entrances, paths, floors and building outlines require field verification by the project team.

### Secrets and Safety
- Never commit `.env` files or secrets.
- Never weaken authentication, authorization, or validation to pass a test.
- See `docs/project/governance/ENGINEERING_RULES.md` for complete rules.

### Stop Conditions
- Stop and request owner review whenever a `docs/project/governance/STOP_CONDITIONS.md` condition is met.

### Deployment
- Do not push, merge, deploy, or modify production resources without explicit owner instruction.

---

## Governance Documents

All governance is in `docs/project/governance/`:

| File | Purpose |
|------|---------|
| `ENGINEERING_RULES.md` | 18 rules governing all implementation work |
| `DEFINITION_OF_DONE.md` | Gates a feature must pass before it is COMPLETE |
| `SPRINT_PROTOCOL.md` | 10-step sequence every sprint must follow |
| `STOP_CONDITIONS.md` | Conditions requiring owner review before proceeding |
| `REPORTING_STANDARD.md` | Structured format for post-sprint reports |
| `GIT_WORKFLOW.md` | Commit / push / merge / deploy confirmation rules |
| `BACKLOG_RULES.md` | How to handle ideas that arise mid-sprint |
| `PROJECT_RESUME_PROMPT.md` | Prompt to re-orient an agent at session start |

---

## Model-Specific Files

`CLAUDE.md` and `GEMINI.md` defer to this file.

Do not create model-specific architecture.

Do not override existing approved decisions unless explicitly asked by the owner.
