# Security — YCT Map

## Status

```
Current phase:     PRE-BUILD / FOUNDATION
Implementation:    NOT STARTED
```

This document records the security model for YCT Map based on approved product decisions.

---

## Authentication

- Normal users (students, staff, visitors) require **no account** for any V1 feature.
- Editors and administrators require authenticated access.
- Editors and administrators use Django's built-in authentication system.
- Editor accounts are created and assigned by administrators; there is no public editor registration.

---

## Authorization

| Action | Who May Perform |
|--------|----------------|
| View map | Anyone |
| Search locations | Anyone |
| Get directions | Anyone |
| Submit a contribution | Anyone (no account required) |
| Review contributions | Authenticated editors and admins |
| Add/edit locations | Authenticated editors and admins |
| Verify locations (FIELD_VERIFIED) | Authenticated editors and admins |
| Manage editor accounts | Authenticated admins |

The contribution submission flow must not require any login.

Verification state changes must not be possible from any unauthenticated request.

---

## Secret Boundaries

| Secret Type | Location |
|-------------|----------|
| Database credentials | Server environment only — never in frontend |
| API keys for tile/routing providers | Server environment (if proxied) or treated as public-safe (if client-side tile URLs) |
| Authentication secrets / JWT signing keys | Server environment only |
| Editor credentials | Server environment / auth provider |

Never commit `.env` files.
Never log passwords, tokens, private keys, database URLs or signed URLs.
Never move backend secrets into frontend code.

---

## Data Ownership

- Campus location data is owned by the project.
- Public contributions are anonymous — no PII is collected from contributors in V1.
- Editor accounts hold minimal PII (email, role, timestamps).
- Contribution data should not expose submitter identity in public-facing views.

---

## Campus Data Integrity

- Demo data must never be exposed as verified campus data in any production-facing context.
- Verification state changes must be deliberate editor actions — never automatic.
- Real YabaTech geographic facts must not be invented or inferred without field confirmation.

---

## Transport Security

- All production traffic must use TLS.
- Never disable TLS verification.

---

## Logging and Redaction

- Do not log passwords, tokens, API keys, database URLs or private keys.
- Do not log personal data from contributors.
- Log security-relevant events (editor logins, failed auth attempts, permission denials).

---

## Known Risks and Deferred Work

- Contribution spam / abuse: strict server-side validation and IP-based rate limiting are the initial V1 controls. CAPTCHA is deferred unless observed abuse or testing demonstrates a need (DEC-T10).
- Editor account recovery: exact operational procedure remains to be defined before editor access is released.
- Detailed API security settings (rate limits, CORS and input validation) will be documented when their endpoints are implemented.

---

## Trust Boundaries

```
[Public Internet]
    |
    | (TLS)
    v
[Frontend / CDN]
    |
    v
[Backend API]  <-- authentication boundary for editor operations
    |
    v
[Database]     <-- internal only; never exposed to public internet
```

## Anonymous contribution controls

The public contribution endpoint requires CSRF, accepts POST only, rejects unknown payload keys, validates controlled choices/references/coordinate ranges and bounds all stored text. A session limit and salted hash of the request IP provide local-development throttling without persisting raw IP addresses. A honeypot absorbs simple automated form posts, while UUID request IDs make retries idempotent. User text is stored as data and rendered with text-only DOM operations or Django's normal escaping.

Moderation remains inside authenticated Django admin. Anonymous submission and moderation are separate capabilities, and no moderation status automatically changes public map data or verification state.
