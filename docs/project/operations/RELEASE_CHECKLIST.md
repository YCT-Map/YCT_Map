# Release Checklist — YCT Map

Reusable checklist to be completed before every production release.

---

## Pre-Release Verification

### Branch and Diff

- [ ] Correct branch is checked out (production branch)
- [ ] Git diff reviewed — only intended changes are present
- [ ] No secrets, private files or unintended generated artifacts in diff
- [ ] Worktree is clean

### Tests

- [ ] Focused tests pass
- [ ] Full regression test suite passes
- [ ] Typecheck passes
- [ ] Production build passes
- [ ] Linter / static checks pass
- [ ] No legitimate test was skipped or weakened

### Migrations

- [ ] Database migrations reviewed
- [ ] Migration is safe (non-destructive or explicitly approved)
- [ ] Rollback migration known
- [ ] Migration tested against a copy of production data if destructive

### Environment

- [ ] `.env.example` matches required production environment variables
- [ ] All required environment variables are set in production
- [ ] No development-only values are present in production

### Demo Data

- [ ] Demo data is not present in production as FIELD_VERIFIED
- [ ] Demo records are correctly labelled DEMO in the database

### Security

- [ ] No secrets committed
- [ ] Authentication and authorization reviewed for the changes being deployed
- [ ] No weakened security in this release

### Deployment

- [ ] Hosting provider is ready
- [ ] Deployment order confirmed: migrations run before application update
- [ ] Health check / readiness endpoint available
- [ ] Rollback procedure is known and confirmed

### Post-Deployment

- [ ] Production smoke test passes
- [ ] Key user flows verified on production: search, routing, contribution submission
- [ ] Monitoring / logging confirms healthy startup
- [ ] Rollback triggered if smoke test fails

---

## Post-Release

- [ ] CHANGELOG.md updated with release milestone
- [ ] CURRENT_STATE.md updated
- [ ] SPRINT_LOG.md entry completed
