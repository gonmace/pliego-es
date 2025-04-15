# flake8: noqa
from .base import *
import os

DEBUG = os.getenv('DJANGO_DEBUG', default=False)

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', default='').split(',')

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
        'NAME': BASE_DIR / 'chromadb',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# Configuración de caché (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Configuración de Celery con Redis
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', default='').split(',')

CSRF_TRUSTED_ORIGINS = ['https://chatlegal.c4all.org']
