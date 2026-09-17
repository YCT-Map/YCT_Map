# Deployment — YCT Map

## Status

```
Current phase:     PRE-BUILD / FOUNDATION
Implementation:    NOT STARTED
Deployment:        NOT STARTED
```

This document will describe the deployment process when it is established.

---

## Confirmed Decisions

- Web application hosting: Render
- Database hosting: Neon PostgreSQL
- Initial deployment URL: Render-provided platform subdomain
- Later custom domain: supported through DNS when acquired or assigned
- Deployment source: designated production branch through GitHub integration

Exact build/start commands, production branch name, migration command, health check and rollback procedure remain to be documented when deployment configuration is implemented.

---

## Expected Deployment Process (Planned)

When the stack is decided, this document will record:

- Production branch
- Build command
- Start command
- Environment variable configuration
- Migration strategy
- Health check / readiness endpoint
- Deployment order (migrations before app)
- Smoke test after deployment
- Rollback procedure

---

## Rules

- Production deployments require explicit owner authorization.
- Migrations must be run before the application is updated.
- A rollback path must be known before any production deployment.
- Never deploy from a branch other than the designated production branch.

---

> Update this document when the hosting provider and CI/CD pipeline are confirmed.
