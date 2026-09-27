# Deployment — YCT Map

## Status

```
Current phase:     PHASE 4 — PHYSICAL ACCEPTANCE PENDING
Implementation:    RENDER/POSTGRESQL CONFIGURATION PREPARED
Deployment:        NOT PERFORMED
```

The first hosted environment is a production candidate for final HTTPS physical-field acceptance. It is not evidence that Phase 4 is closed or that campus data is field verified.

## Confirmed Architecture

- Source control: GitHub organization repository, after separate owner authorization.
- Web service: Render Python web service.
- Database: PostgreSQL supplied through `DATABASE_URL`; the selected PostgreSQL provider can be connected without application changes.
- Application server: Gunicorn serving `yctmap.wsgi:application`.
- Static files: Django `collectstatic` plus WhiteNoise compressed manifest storage.
- Health check: `GET /health/`.
- Local development: SQLite remains supported and development Quick Tunnels remain development-only.

## Render Contract

`render.yaml` defines:

- build command: `bash build.sh`;
- start command: `gunicorn yctmap.wsgi:application --bind 0.0.0.0:$PORT`;
- health-check path: `/health/`;
- production environment selection;
- generated Django secret;
- externally supplied `DATABASE_URL`;
- trusted reverse-proxy HTTPS handling.

`build.sh` installs locked dependencies, collects static files and applies migrations. A failed command stops the build.

## Required Environment

- `APP_ENV=production`
- `DJANGO_SECRET_KEY`: unique generated private value
- `DATABASE_URL`: private PostgreSQL connection URL
- `TRUST_PROXY_HTTPS=1` on Render
- `RENDER_EXTERNAL_HOSTNAME`: supplied automatically by Render
- optional `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for later custom domains

Production refuses to start without `DJANGO_SECRET_KEY` or `DATABASE_URL`. Secure cookies, HTTPS redirection, content-type protection and a conservative HSTS policy are enabled outside development.

## SQLite-to-PostgreSQL Data Transfer

1. Freeze and hash a verified cleaned SQLite backup.
2. Run all Django migrations against an empty PostgreSQL database.
3. Export application data and auth users using Django natural-key serialization, excluding regenerated content types, permissions, sessions and nonessential admin logs.
4. Load the data into PostgreSQL and reset integer sequences.
5. Compare per-model counts, UUIDs, foreign-key relationships, password hashes, routing provenance, contribution history and private survey evidence.
6. Run authentication, public-search, routing, Editor, Admin and field-survey smoke tests.
7. Retain the source SQLite backup until owner acceptance.

The migration must be rehearsed before deployment. PostgreSQL is not yet populated, and no production resource has been created.

## Rollback

- Keep the last successful Render deployment available.
- Keep a verified pre-transfer SQLite backup and a PostgreSQL backup/export.
- Do not destroy the source database until the hosted data has passed count, integrity and owner checks.
- If migration or smoke tests fail, stop deployment and restore the previous application/database pair rather than editing production data ad hoc.

## Rules

- Deployment requires explicit owner authorization.
- Never commit secrets or a populated database.
- Never load DEMO fixtures into production.
- Never equate successful deployment with physical or field verification.
- No push or deployment is authorized by this preparation work.
