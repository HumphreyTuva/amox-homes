import os
import sys
from django.core.exceptions import ImproperlyConfigured
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
# Safe by default: DEBUG is on only for local `manage.py` commands. The live web server (gunicorn etc.)
# runs with DEBUG off and refuses to start without SECRET_KEY and ALLOWED_HOSTS.
DEBUG = os.getenv("DEBUG", "1" if os.path.basename(sys.argv[0]) == "manage.py" else "0") == "1"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me" if DEBUG else "")
ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "*" if DEBUG else "").split(",") if h]
if not DEBUG and not (SECRET_KEY and ALLOWED_HOSTS):
    raise ImproperlyConfigured("Set SECRET_KEY and ALLOWED_HOSTS environment variables.")
CSRF_TRUSTED_ORIGINS = [o for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "django.contrib.sitemaps", "rest_framework", "core",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "amox.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "core.context.site",
    ]},
}]
WSGI_APPLICATION = "amox.wsgi.application"
DATABASES = {"default": dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = False
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_MEMORY_SIZE = 60 * 1024 * 1024  # videos
LOGIN_URL = "/admin/login/"

# AMOX contact details
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "254180280179")
PHONE = "0180280179"
EMAIL = "amoxhomes@gmail.com"
# Lead alerts go to EMAIL. Without SMTP settings they print to the console (fine for development).
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend" if os.getenv("EMAIL_HOST") else "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL)

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_THROTTLE_RATES": {"leads": "30/hour"},
}
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SSL_REDIRECT", "1") == "1"
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
