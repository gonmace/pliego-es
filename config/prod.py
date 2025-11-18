# prod.py
from .base import *
import os

DEBUG = os.getenv('DJANGO_DEBUG', default=False)

ALLOWED_HOSTS = [host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]

INSTALLED_APPS += [

]

# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': '5432',
    },
    'chromadb': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'chroma_db',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# Configuración de caché (memoria local - suficiente si no se necesita cache distribuido)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Celery no está instalado - si se necesita en el futuro, instalar celery y redis
# CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
# CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', default='').split(',')

CSRF_TRUSTED_ORIGINS = ['https://pliego.magoreal.com']
