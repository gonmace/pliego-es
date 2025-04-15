# flake8: noqa
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS += [
    # "django_extensions",
    # "debug_toolbar",
    'django_browser_reload',
]

MIDDLEWARE += [
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', default='base'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': '127.0.0.1',
        'PORT': os.getenv('POSTGRES_PORT')
    },
    'chromadb': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'chromadb',
    }
}

TAILWIND_APP_NAME = 'theme'

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = BASE_DIR / "sent_emails"

CSRF_COOKIE_SECURE = False

CSRF_USE_SESSIONS = False

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}


CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:4321",  # tu frontend Astro
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:4321",  # dominio de tu frontend Astro
]