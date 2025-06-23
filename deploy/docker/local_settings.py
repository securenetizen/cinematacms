import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.abspath('.')

FRONTEND_HOST = os.getenv('FRONTEND_HOST', 'http://localhost')
PORTAL_NAME = os.getenv('PORTAL_NAME', 'CinemataCMS')
SECRET_KEY = os.getenv('SECRET_KEY', 'ma!s3^b-cw!f#7s6s0m3*jx77a@riw(7701**(r=ww%w!2+yk2')
REDIS_LOCATION = os.getenv('REDIS_LOCATION', 'redis://redis:6379/1')

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('POSTGRES_NAME', 'cinematacms'),
        "HOST": os.getenv('POSTGRES_HOST', 'db'),
        "PORT": os.getenv('POSTGRES_PORT', '5432'),
        "USER": os.getenv('POSTGRES_USER', 'cinematacms'),
        "PASSWORD": os.getenv('POSTGRES_PASSWORD', 'cinematacms'),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_LOCATION,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# CELERY STUFF
BROKER_URL = REDIS_LOCATION
CELERY_RESULT_BACKEND = BROKER_URL

MP4HLS_COMMAND = "/home/cinemata/bento4/bin/mp4hls"

DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY=os.getenv('SECRET_KEY')
LOCAL_INSTALL=True
DEBUG = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, 'static_collected')


# Upload subdomain configuration
UPLOAD_SUBDOMAIN = os.getenv('UPLOAD_SUBDOMAIN', 'upload.cinemata.local')

# Extract domain from FRONTEND_HOST for ALLOWED_HOSTS
import re
FRONTEND_DOMAIN = re.sub(r'^https?://', '', FRONTEND_HOST)

# Configure ALLOWED_HOSTS to include both main domain and upload subdomain
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    FRONTEND_DOMAIN,
    UPLOAD_SUBDOMAIN,
    # Allow any subdomain of the main domain
    f'.{FRONTEND_DOMAIN}' if '.' in FRONTEND_DOMAIN else FRONTEND_DOMAIN,
]

# Remove duplicates and empty entries
ALLOWED_HOSTS = list(filter(None, list(set(ALLOWED_HOSTS))))

# CSRF Trusted Origins for upload subdomain
CSRF_TRUSTED_ORIGINS = []
# Dynamic CSRF trusted origins
CSRF_TRUSTED_ORIGINS.extend([
    f"http://{FRONTEND_DOMAIN}",
    f"https://{FRONTEND_DOMAIN}",
    f"http://{UPLOAD_SUBDOMAIN}",
    f"https://{UPLOAD_SUBDOMAIN}",
])