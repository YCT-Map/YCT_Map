# Environment — YCT Map

## Status

```
Current phase:     PRE-BUILD / FOUNDATION
Implementation:    NOT STARTED
```

Environment variables will be documented here as the stack is decided and implemented.

A `.env.example` file must be maintained at the repository root once the backend is set up.

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

These are indicative based on the planned architecture. Actual variables will be confirmed during implementation.

| Name | Purpose | Environment | Classification |
|------|---------|-------------|----------------|
| `DATABASE_URL` | Database connection string | Server | SERVER-PRIVATE |
| `DJANGO_SECRET_KEY` | Django cryptographic signing secret | Server | SERVER-PRIVATE |
| `DJANGO_SETTINGS_MODULE` | Django settings module selection | Server | PUBLIC |
| `APP_ENV` | Environment name (development, production) | Server | PUBLIC |

OpenFreeMap's approved Liberty style URL does not currently require an application API key. All variable names remain indicative until the Django foundation is implemented and `.env.example` is created.

---

## Rules

- Never commit `.env` files.
- Maintain `.env.example` with placeholder values only.
- Never log actual environment variable values.
- Compare `.env.example` against real environment before deployment.
