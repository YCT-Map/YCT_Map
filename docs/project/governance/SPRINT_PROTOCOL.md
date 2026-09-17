# Sprint Protocol

Every build sprint follows this sequence.

## 1. Resume

Read:

1. CURRENT_STATE.md
2. PROJECT_BRIEF.md
3. BUILD_PIPELINE.md
4. ARCHITECTURE.md
5. DECISIONS.md
6. latest SPRINT_LOG.md entry
7. relevant feature documentation

Then inspect the repository.

## 2. Understand

Before implementation, state:

- sprint objective;
- current relevant architecture;
- files likely involved;
- dependencies;
- risks;
- open decisions.

## 3. Plan

Produce a narrow implementation plan.

Separate:

- required work;
- optional improvements;
- deferred ideas.

Do not begin material architecture changes without approval.

## 4. Implement

Work in small coherent increments.

Preserve existing behavior.

Avoid unrelated refactors.

## 5. Verify

Run:

- focused tests;
- relevant regression tests;
- typecheck;
- build;
- other project-specific gates.

## 6. Inspect

Review:

- git diff;
- changed files;
- accidental changes;
- secret exposure;
- schema/migration changes.

## 7. Document

Update:

- CURRENT_STATE.md
- SPRINT_LOG.md

and any affected architecture/API/schema/environment documents.

## 8. Report

Return:

- objective;
- implemented work;
- files changed;
- tests;
- unresolved issues;
- decisions;
- risks;
- next recommended step.

## 9. Commit

Commit only if authorized.

Use a clear commit message describing the actual change.

## 10. Stop

Do not automatically start the next sprint unless explicitly instructed.
