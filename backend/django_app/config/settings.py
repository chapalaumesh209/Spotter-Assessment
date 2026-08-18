import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-fuel-optimal-route-planner-key-2026')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'fuel_optimizer.apps.FuelOptimizerConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'UNAUTHENTICATED_USER': None,
}

# Fuel Optimization & Routing Settings
OSRM_BASE_URL = os.environ.get('OSRM_BASE_URL', 'http://router.project-osrm.org')
CENSUS_GEOCODER_URL = os.environ.get('CENSUS_GEOCODER_URL', 'https://geocoding.geo.census.gov/geocoder')
NOMINATIM_URL = os.environ.get('NOMINATIM_URL', 'https://nominatim.openstreetmap.org/search')

ROUTE_CORRIDOR_MILES = float(os.environ.get('ROUTE_CORRIDOR_MILES', 25.0))
MAX_RANGE_MILES = float(os.environ.get('MAX_RANGE_MILES', 500.0))
MPG = float(os.environ.get('MPG', 10.0))
TANK_CAPACITY_GALLONS = float(os.environ.get('TANK_CAPACITY_GALLONS', 50.0))

# Fallback path lookup
_app_data = os.path.join(BASE_DIR, 'fuel_optimizer', 'data', 'processed_fuel_prices.csv')
_backend_data = os.path.join(BASE_DIR.parent, 'data', 'processed_fuel_prices.csv')
PROCESSED_DATA_PATH = _app_data if os.path.exists(_app_data) else _backend_data

ORIGINAL_CSV_PATH = os.path.join(PROJECT_ROOT, 'fuel-prices-for-be-assessment.csv')
