# Git Workflow

## General

- Work on a dedicated feature/sprint branch.
- Keep main deployable.
- Avoid unrelated changes in one commit.
- Prefer meaningful commits at stable checkpoints.

## Prohibited Without Explicit Approval

- force push;
- history rewrite;
- rebasing published work;
- deleting protected tags;
- destructive reset;
- direct production deployment;
- deleting remote branches used for active review.

## Before Commit

Confirm:

- tests pass;
- build passes;
- diff reviewed;
- no secrets;
- no private files;
- no accidental generated artifacts.

## Before Push

Confirm:

- correct branch;
- correct remote;
- clean expected history;
- no unexpected divergence.

## Before Merge

Confirm:

- reviewed diff;
- required checks green;
- no conflicts;
- production branch target correct.

## Before Deployment

Confirm:

- intended commit is on production branch;
- migration strategy known;
- environment contract known;
- rollback path known;
- production smoke test defined.
