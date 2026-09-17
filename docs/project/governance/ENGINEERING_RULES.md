# Engineering Rules

These rules govern all implementation work in this repository.

## 1. Inspect Before Editing

Before modifying code:

- inspect the relevant files;
- understand existing abstractions;
- trace affected data flows;
- identify existing tests;
- check related documentation.

Do not assume the architecture from filenames alone.

## 2. Do Not Invent Missing Architecture

If an implementation requires a material architectural, product, security, or data-model decision that has not already been made:

STOP and request owner approval.

Do not silently choose:

- a new database;
- a new state-management system;
- a new authentication model;
- a new hosting provider;
- a new API architecture;
- a new external service;
- a paid dependency.

## 3. Reuse Before Creating

Prefer existing:

- utilities;
- components;
- hooks;
- services;
- schemas;
- validation;
- API clients;
- design patterns.

Do not create parallel abstractions unless the existing one is demonstrably unsuitable.

## 4. Keep Scope Narrow

Implement only the approved task.

Do not use a small feature request as permission to:

- redesign unrelated screens;
- refactor unrelated modules;
- replace working libraries;
- rewrite architecture;
- introduce speculative infrastructure.

Put useful unrelated ideas in BACKLOG.md.

## 5. No Fake Implementations

Do not mark something complete if it:

- uses placeholder data where real data is required;
- pretends verification occurred when it did not;
- returns mocked success in production code;
- skips persistence that the feature requires;
- implements only the happy path while claiming feature completion.

Temporary mocks must be explicitly labelled and isolated.

## 6. Never Weaken Safety to Pass

Never solve a failure by silently:

- removing validation;
- weakening authentication;
- weakening authorization;
- disabling TLS verification;
- changing readiness checks to always pass;
- deleting failing tests;
- increasing timeouts without diagnosis;
- swallowing errors;
- exposing secrets.

Find the actual cause.

## 7. Data Integrity Comes First

Before changing persistent data structures:

- inspect existing schema and migrations;
- identify compatibility impact;
- identify rollback implications;
- preserve historical data unless deletion is explicitly approved.

Never rewrite an already-applied migration unless the repository explicitly uses that model.

## 8. Secrets

Never:

- commit .env files;
- print private environment variables;
- log passwords, tokens, private keys, database URLs, or signed URLs;
- move backend secrets into frontend code.

Use placeholders in documentation.

## 9. Error Handling

Errors should:

- fail clearly;
- preserve useful diagnostic information;
- avoid leaking secrets or internal implementation details to users;
- use existing application error conventions.

Do not silently recover from a state that may cause corruption.

## 10. Testing

Every material implementation should include appropriate tests.

Never delete or weaken a legitimate test solely to make the suite pass.

When a test fails:

1. determine whether it is a product defect;
2. determine whether it is a test defect;
3. determine whether it is an environment/tooling defect;
4. fix the correct layer.

## 11. Build Verification

Before declaring work complete, run the relevant:

- focused tests;
- regression tests;
- typecheck;
- production build;
- lint/static checks;
- git diff check.

Use the project's documented gates.

## 12. Documentation Is Part of the Build

Update relevant project documentation when implementation changes:

- architecture;
- environment contract;
- API behavior;
- schema;
- build state;
- known limitations.

Documentation should reflect reality, not plans that were never implemented.

## 13. No Silent Repairs

If something unexpected happens, report it.

Do not silently:

- normalize stored data;
- rewrite checksums;
- alter schema;
- remove user data;
- switch dependencies;
- change environment assumptions.

## 14. Prefer Explicit Over Clever

Choose understandable, maintainable code over sophisticated abstractions with little practical benefit.

Optimize for future developers being able to understand the system.

## 15. Preserve Existing Working Behavior

A new feature must not casually regress existing functionality.

Check affected flows and preserve backwards compatibility where required.

## 16. External Services

Before introducing an external dependency, identify:

- why it is required;
- cost implications;
- security implications;
- lock-in;
- failure behavior;
- development/testing story.

Owner approval is required for material new dependencies.

## 17. Worktree Discipline

Before major transitions:

- inspect git status;
- know the current branch;
- ensure private/untracked files are not accidentally included.

After implementation:

- inspect the complete diff;
- ensure only intended files changed.

## 18. Do Not Deploy Without Authorization

Code completion does not imply authorization to:

- push;
- merge;
- deploy;
- migrate production;
- modify production environment variables;
- rotate secrets;
- delete production resources.

These require explicit owner instruction.
