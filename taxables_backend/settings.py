# taxables_backend/settings.py
import os
from pathlib import Path
from corsheaders.defaults import default_headers
import dj_database_url

# ---------------- Base ----------------
BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-only")

# Optional: your custom API domain (set on Render if you map GoDaddy)
CUSTOM_API_DOMAIN = os.getenv("CUSTOM_API_DOMAIN", "").strip()  # e.g. api.yourdomain.com

# Render injects this automatically
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()

# Local Expo web origins (dev only)
EXPO_WEB_ORIGINS = os.getenv(
    "EXPO_WEB_ORIGINS",
    "http://localhost:19006,http://127.0.0.1:19006,"
    "http://localhost:8081,http://127.0.0.1:8081"
).split(",")

# ---------------- Hosts / CSRF / CORS ----------------
if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    # allow what you set + the render host + optional custom domain
    ALLOWED_HOSTS = [
        h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()
    ]
    if RENDER_HOST and RENDER_HOST not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_HOST)
    if CUSTOM_API_DOMAIN and CUSTOM_API_DOMAIN not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(CUSTOM_API_DOMAIN)

# CSRF: schemes are required
CSRF_TRUSTED_ORIGINS = []
# allow local web origins during dev (only relevant if you use cookie auth/forms on web)
CSRF_TRUSTED_ORIGINS += [o for o in EXPO_WEB_ORIGINS if o]
if RENDER_HOST:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOST}")
if CUSTOM_API_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{CUSTOM_API_DOMAIN}")

# CORS: for a pure native app this is usually not needed; permissive is fine
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    "ngrok-skip-browser-warning",  # harmless if unused
]

# ---------------- Apps / Middleware ----------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "core",
    "django_filters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # static files in prod
    "corsheaders.middleware.CorsMiddleware",        # keep before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "taxables_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "taxables_backend.wsgi.application"

# ---------------- Database ----------------
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=0 if DEBUG else 600,
        ssl_require=True,
    )
}

# ---------------- Internationalization ----------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------- Static / Media (WhiteNoise) ----------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    }
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------- DRF / Auth / Filters ----------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],  
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ] + (["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else []),
}

# (optional) tune JWT lifetimes later if you want
from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------- Security behind proxy ----------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# ---------------- Logging (concise) ----------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ---------------- Misc ----------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Health endpoint you mentioned
HEALTHCHECK_PATH = "/api/health/"
