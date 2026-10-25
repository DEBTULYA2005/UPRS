"""
Django settings for the Universal Recommendation System backend.

All secrets and environment-specific values come from environment variables
(or a local `.env` file, which is git-ignored). Nothing sensitive is hardcoded.
"""

import os
import sys
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
DEBUG = env_bool("DEBUG", False)
TESTING = "test" in sys.argv

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = "insecure-local-development-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured(
            "SECRET_KEY is not set. Generate one with: "
            'python -c "from django.core.management.utils import get_random_secret_key; '
            'print(get_random_secret_key())"'
        )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Render sets this automatically for web services.
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    # project apps
    "clients",
    "content",
    "interactions",
    "recommendations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

# --------------------------------------------------------------------------
# Database (PostgreSQL via DATABASE_URL - Supabase or Render)
# --------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "")
if TESTING:
    # `manage.py test` never touches your hosted database. Django creates a
    # throw-away test database. Point TEST_DATABASE_URL at a LOCAL PostgreSQL
    # for the most realistic run; otherwise an in-memory SQLite DB is used.
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://:memory:")
if not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in your "
        "PostgreSQL connection string (see README.md)."
    )

_db = dj_database_url.parse(DATABASE_URL, conn_max_age=600, conn_health_checks=True)

if "postgresql" in _db["ENGINE"]:
    _host = (_db.get("HOST") or "").lower()
    _is_local = _host in {"", "localhost", "127.0.0.1", "::1"}
    # Supabase and Render external connections require SSL. Local Postgres usually doesn't.
    if env_bool("DATABASE_SSL_REQUIRE", default=not _is_local):
        _db.setdefault("OPTIONS", {})["sslmode"] = "require"
    # Supabase "transaction" pooler (port 6543, pgbouncer) does not support
    # server-side cursors or prepared statements. Set this to true if you use it.
    if env_bool("DATABASE_USING_TRANSACTION_POOLER", False):
        _db["DISABLE_SERVER_SIDE_CURSORS"] = True
        _db.setdefault("OPTIONS", {})["prepare_threshold"] = None

DATABASES = {"default": _db}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Static files (Django admin CSS, served by WhiteNoise)
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
if TESTING or DEBUG:
    STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}

# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------
# Example: CORS_ALLOWED_ORIGINS=http://localhost:5173,https://my-shop.example.com
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
from corsheaders.defaults import default_headers  # noqa: E402

CORS_ALLOW_HEADERS = list(default_headers) + ["x-api-key"]

# --------------------------------------------------------------------------
# Django REST Framework + API docs
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["clients.authentication.ClientApiKeyAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["clients.permissions.IsAuthenticatedClient"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Universal Recommendation System API",
    "DESCRIPTION": (
        "Multi-client recommendation backend. Every endpoint except /api/health/ "
        "requires an `X-API-Key` header. Keys are issued per client and are "
        "never accepted in the request body."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVE_AUTHENTICATION": [],
}

# --------------------------------------------------------------------------
# Security headers for production (Render terminates TLS in front of Gunicorn)
# --------------------------------------------------------------------------
if not DEBUG and not TESTING:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)

# --------------------------------------------------------------------------
# Logging (never log request headers/bodies -> API keys cannot leak here)
# --------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}
