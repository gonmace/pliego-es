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

# Configuración de base de datos
# Siempre usar pliego-db (puerto 5433 cuando está fuera de Docker, puerto 5432 dentro de Docker)
# NO usar esp-db que está en el puerto 5432 del host
postgres_host = os.getenv('POSTGRES_HOST', default='127.0.0.1')
postgres_port_env = os.getenv('POSTGRES_PORT', default='5433')

# Si el host es 'pliego-db', verificar si estamos dentro o fuera de Docker
if postgres_host == 'pliego-db':
    try:
        import socket
        socket.gethostbyname('pliego-db')
        # Si resuelve, estamos dentro de Docker, usar el nombre del contenedor y puerto interno
        postgres_host = 'pliego-db'
        postgres_port = '5432'  # Puerto interno del contenedor
    except socket.gaierror:
        # No resuelve, estamos fuera de Docker, usar localhost y puerto expuesto
        postgres_host = '127.0.0.1'
        postgres_port = '5433'  # Puerto expuesto de pliego-db (NO 5432 que es esp-db)
else:
    # Si estamos fuera de Docker (host es 127.0.0.1 o localhost)
    # SIEMPRE usar puerto 5433 para pliego-db, nunca 5432 que es esp-db
    if postgres_host in ('127.0.0.1', 'localhost'):
        postgres_port = '5433'  # Forzar puerto de pliego-db
    else:
        # Si se especifica otro host, usar el puerto del env o por defecto 5433
        if postgres_port_env == '5432':
            # Si está intentando usar 5432 (esp-db), cambiarlo a 5433 (pliego-db)
            postgres_port = '5433'
        else:
            postgres_port = postgres_port_env

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', default='base'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': postgres_host,
        'PORT': postgres_port
    },
    'chroma_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'chroma_db',
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
    "https://36d2f6f941b2.ngrok-free.app",  # ngrok tunnel (sin barra final)
]