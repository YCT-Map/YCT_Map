# Environment — YCT Map

## Status

```
Current phase:     PHASE 4 — PRE-CLOSEOUT
Implementation:    LOCAL DEVELOPMENT + OPTIONAL HTTPS FIELD-TEST TUNNEL CONTRACT ACTIVE
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
| `DATABASE_URL` | PostgreSQL connection string in production; SQLite is the development fallback only | Server | SERVER-PRIVATE |
| `DJANGO_SECRET_KEY` | Django cryptographic signing secret | Server | SERVER-PRIVATE |
| `DJANGO_SETTINGS_MODULE` | Django settings module; defaults to `yctmap.settings` | Server | PUBLIC |
| `APP_ENV` | Environment name; defaults to `development` | Server | PUBLIC |
| `DEV_TUNNEL_HOST_SUFFIX` | Optional development-only ephemeral tunnel suffix; defaults to `.trycloudflare.com`, set empty to disable | Server | PUBLIC |
| `ALLOWED_HOSTS` | Optional comma-separated additional production hostnames | Server | PUBLIC |
| `CSRF_TRUSTED_ORIGINS` | Optional comma-separated trusted HTTPS origins | Server | PUBLIC |
| `RENDER_EXTERNAL_HOSTNAME` | Render-provided service hostname, incorporated automatically | Server | PLATFORM-PROVIDED |
| `TRUST_PROXY_HTTPS` | Enables trusted reverse-proxy HTTPS recognition when set to `1` | Server | PUBLIC |
| `SECURE_HSTS_SECONDS` | Production HSTS duration; defaults to one hour | Server | PUBLIC |

OpenFreeMap's approved Liberty style URL does not require an application API key. Development uses local SQLite at `db.sqlite3`, which is Git-ignored. Production refuses to start without both `DJANGO_SECRET_KEY` and `DATABASE_URL`.

In development only, the configured `.trycloudflare.com` suffix expands Django `ALLOWED_HOSTS` and HTTPS `CSRF_TRUSTED_ORIGINS` so a phone can reach the local server through an ephemeral Cloudflare Quick Tunnel. Localhost remains supported. Production settings do not inherit the wildcard, and the tunnel is not a deployment, authentication substitute or permanent origin.

---

## Rules

- Never commit `.env` files.
- Maintain `.env.example` with placeholder values only.
- Never log actual environment variable values.
- Compare `.env.example` against real environment before deployment.
