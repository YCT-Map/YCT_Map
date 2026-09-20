# YCT Map — Project Documentation

This directory contains all project documentation for YCT Map.

## Learning Record

| Document | Purpose |
|----------|---------|
| [`BUILD_JOURNAL.md`](BUILD_JOURNAL.md) | Student-facing explanation of how accepted sprint work was built, how it functions, and why technical decisions were made |

---

## Documentation Authority Model

Repository code is **authoritative** for what is currently implemented.
Project documentation is **authoritative** for approved intent and process.

When code and documentation conflict:
1. Do not silently choose.
2. Identify whether documentation is stale or the implementation is incorrect.
3. Report the conflict.
4. Update only after resolving the discrepancy.

| Level | Source | Authority Over |
|-------|--------|---------------|
| **1 — Governance** | `governance/` and `AGENTS.md` | Agent and developer behavior |
| **2 — Approved Product Intent** | `product/` and `operations/DECISIONS.md` | What YCT Map is supposed to become |
| **3 — Approved Technical Intent** | `technical/` | Accepted architecture and technical decisions |
| **4 — Repository Reality** | Source code, migrations, config, tests | What currently exists |

---

## Minimum Resume Set

For most tasks, read these before touching code:

1. `operations/CURRENT_STATE.md`
2. `product/PROJECT_BRIEF.md`
3. `product/V1_SCOPE.md`
4. `operations/DECISIONS.md`
5. Latest entry in `operations/SPRINT_LOG.md`
6. Documentation directly related to the requested task

Then inspect the actual repository source code.

Do not read every document for every minor task.

---

## Document Index

### governance/ — Project Governance

Update rarely. Change only with owner/team consensus.

| Document | Purpose | Update Frequency |
|----------|---------|-----------------|
| `ENGINEERING_RULES.md` | 18 rules governing all implementation work | Rarely |
| `DEFINITION_OF_DONE.md` | Gates a feature must pass before it is COMPLETE | Rarely |
| `SPRINT_PROTOCOL.md` | 10-step sprint sequence | Rarely |
| `STOP_CONDITIONS.md` | 17 conditions requiring owner review | Rarely |
| `REPORTING_STANDARD.md` | Post-sprint report format | Rarely |
| `GIT_WORKFLOW.md` | Git safety rules | Rarely |
| `BACKLOG_RULES.md` | Scope discipline rules | Rarely |
| `PROJECT_RESUME_PROMPT.md` | Prompt to re-orient an agent at session start | Rarely |

---

### product/ — Approved Product Intent

Defines what YCT Map is supposed to become. Do not redefine without owner approval.

| Document | Purpose | Update Frequency |
|----------|---------|-----------------|
| `PROJECT_BRIEF.md` | Product overview, users, goals, constraints | Rarely |
| `V1_SCOPE.md` | V1 features and explicit non-goals | Rarely |
| `UX_FLOW.md` | User journey through the application | Occasionally |
| `EDITOR_WORKFLOW.md` | Editor and admin capabilities and review actions | Occasionally |
| `ROADMAP.md` | V1, V1.1, V2, Later milestones | Occasionally |
| `DESIGN_SYSTEM.md` | Visual direction and UI principles | Occasionally |

---

### technical/ — Approved Technical Intent

Records technical architecture decisions. Must distinguish CURRENT from PLANNED.

| Document | Purpose | Update Frequency |
|----------|---------|-----------------|
| `ARCHITECTURE.md` | System overview and technology decisions | Per major sprint |
| `DATA_MODEL.md` | Database entities, relationships, invariants | Per schema change |
| `ROUTING.md` | Routing behavior and scope | Occasionally |
| `API_CONTRACT.md` | Backend API routes and contracts | Per implemented route |
| `SECURITY.md` | Auth model, secret boundaries, trust model | Per auth/security change |
| `ENVIRONMENT.md` | Environment variables and classification | Per env change |
| `DEPLOYMENT.md` | Deployment process and hosting | Per deployment change |
| `TEST_STRATEGY.md` | Testing approach, frameworks, gates | Per test infrastructure change |
| `CODE_STYLE.md` | Code conventions for this repository | Per convention change |

### phase4/ — Approved Phase 4 Product/Data Contract

| Document | Purpose | Update Frequency |
|----------|---------|-----------------|
| [`CAMPUS_DATA_AND_EDITOR_SPEC.md`](phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md) | Authoritative campus-place, entrance, internal-place and editor-workflow baseline | Only through explicit owner change control |

---

### operations/ — Current State and History

Updated frequently. Living records of project state.

| Document | Purpose | Update Frequency |
|----------|---------|-----------------|
| `CURRENT_STATE.md` | Current phase, branch, blockers, next task | Every sprint |
| `BUILD_PIPELINE.md` | Phase-by-phase build plan with status | Per phase change |
| `DECISIONS.md` | Material decisions (ADR format) | When decisions are made |
| `SPRINT_LOG.md` | Append-only sprint history | Every sprint |
| `KNOWN_ISSUES.md` | Bugs, limitations, technical debt | As discovered |
| `RISKS.md` | Material project risks | As identified |
| `BACKLOG.md` | Ideas not in current sprint | As ideas arise |
| `RELEASE_CHECKLIST.md` | Pre/post-release gates | Rarely |
| `CHANGELOG.md` | Product milestone history | Per release |
