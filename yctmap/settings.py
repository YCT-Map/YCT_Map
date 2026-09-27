"""Django settings for YCT Map."""

import os
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

APP_ENV = os.environ.get("APP_ENV", "development").strip().lower()
DEBUG = APP_ENV != "production"

_development_secret = secrets.token_urlsafe(50)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", _development_secret)
if not DEBUG and SECRET_KEY == _development_secret:
    raise RuntimeError("DJANGO_SECRET_KEY must be set outside local development.")

def _split_environment_list(name):
    return [value.strip() for value in os.environ.get(name, "").split(",") if value.strip()]


ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"] if DEBUG else []
ALLOWED_HOSTS.extend(_split_environment_list("ALLOWED_HOSTS"))
CSRF_TRUSTED_ORIGINS = _split_environment_list("CSRF_TRUSTED_ORIGINS")

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# Optional development-only wildcard for ephemeral HTTPS field-test tunnels.
# A leading dot is Django's documented subdomain wildcard for ALLOWED_HOSTS.
DEV_TUNNEL_HOST_SUFFIX = os.environ.get("DEV_TUNNEL_HOST_SUFFIX", ".trycloudflare.com").strip()


def _development_tunnel_config(app_env, suffix):
    if app_env == "production" or not suffix:
        return (), ()
    return (suffix,), (f"https://*{suffix}",)


dev_hosts, dev_origins = _development_tunnel_config(APP_ENV, DEV_TUNNEL_HOST_SUFFIX)
ALLOWED_HOSTS.extend(dev_hosts)
CSRF_TRUSTED_ORIGINS.extend(dev_origins)

# Cloudflare terminates HTTPS before forwarding to the local development server.
# Production enables this only when its trusted reverse proxy is configured to
# overwrite, rather than merely pass through, X-Forwarded-Proto.
TRUST_PROXY_HTTPS = DEBUG or os.environ.get("TRUST_PROXY_HTTPS", "").strip() == "1"
if TRUST_PROXY_HTTPS:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_FAILURE_VIEW = "yctmap.views.csrf_failure"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "locations.apps.LocationsConfig",
    "routing.apps.RoutingConfig",
    "contributions.apps.ContributionsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "yctmap.middleware.EditorNoStoreMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "yctmap.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "yctmap.wsgi.application"
ASGI_APPLICATION = "yctmap.asgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=not DEBUG,
        )
    }
elif DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    raise RuntimeError("DATABASE_URL must be set in production.")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        },
    }

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "3600")) if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/editor/login/"
LOGIN_REDIRECT_URL = "/editor/"
