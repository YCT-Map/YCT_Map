# Environment — YCT Map

## Status

```
Current phase:     PHASE 1 — FOUNDATION & MAP EXPERIENCE
Implementation:    LOCAL DEVELOPMENT CONTRACT ACTIVE
```

The repository includes `.env.example`. Local development works without copying it; non-local environments must supply their own private secret.

---

## Classification

| Classification | Meaning |
|----------------|---------|
| PUBLIC | Safe to expose; no security risk |
| FRONTEND-SAFE | May be used in frontend code (e.g., public tile API keys) |
| SERVER-PRIVATE | Must never leave the server environment |
| PLATFORM-PROVIDED | Injected by the hosting platform; not manually set |

---

## Known / Expected Environment Variables

Current and planned variables:

| Name | Purpose | Environment | Classification |
|------|---------|-------------|----------------|
| `DATABASE_URL` | Future PostgreSQL connection string; not consumed in Sprint 001 | Server | SERVER-PRIVATE |
| `DJANGO_SECRET_KEY` | Django cryptographic signing secret | Server | SERVER-PRIVATE |
| `DJANGO_SETTINGS_MODULE` | Django settings module; defaults to `yctmap.settings` | Server | PUBLIC |
| `APP_ENV` | Environment name; defaults to `development` | Server | PUBLIC |

OpenFreeMap's approved Liberty style URL does not require an application API key. Sprint 001 uses local SQLite at `db.sqlite3`, which is Git-ignored.

---

## Rules

- Never commit `.env` files.
- Maintain `.env.example` with placeholder values only.
- Never log actual environment variable values.
- Compare `.env.example` against real environment before deployment.
