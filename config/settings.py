import os

import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)

PROJECT_DIRNAME = PROJECT_ROOT.split(os.sep)[-1]

SECRET_KEY = os.environ.get('SECRET_KEY', 'smhp$3)1*fzc8(ptv_1**kmtq!z+o^9)dsy(u8iijyeo&$(+mn')

DEBUG = True

ENV = os.environ.get('ENVIRONMENT', 'local')

SITE_ID = 1

ALLOWED_HOSTS = ['127.0.0.1']

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_extensions',
    'rest_framework',
    'oauth2_provider',

    'apps.authenticate',
    'apps.calendar',
)

MIDDLEWARE_CLASSES = (

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',

)

ROOT_URLCONF = 'config.urls'
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'oauth2_provider.backends.OAuth2Backend',

)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, "templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',

            ],
        },
    },
]
WSGI_APPLICATION = 'config.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination'
}

if ENV == 'local':
    db_type = os.environ.get('DB_TYPE')
    if db_type == "postgres":
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'calendar',
                'USER': 'admin',
                'PASSWORD': os.environ.get('SQL_PWD'),
                'HOST': 'localhost',
                'PORT': '5432'
            }
        }
    elif db_type == "sqlite":
        DATABASES = {
            'default': dj_database_url.parse(os.environ.get('DATABASE_URL')),
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'calendar_db',
                'USER': 'calendar_admin',
                'PASSWORD': os.environ.get('SQL_PWD'),
                'HOST': "127.0.0.1",  # Or an IP Address that your DB is hosted on
                'PORT': '3306',
            }
        }
else:
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL')
        )
    }

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

if ENV == 'local':
    STATICFILES_DIRS = (
        os.path.join(PROJECT_ROOT, "static"),
    )
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    STATIC_ROOT = os.path.join((BASE_DIR), 'static')

MEDIA_ROOT = os.path.join(PROJECT_ROOT, "static", "mediaroot")

MEDIA_URL = '/media/'

CALENDAR_CLIENT_ID = os.environ.get('CALENDAR_CLIENT_ID')
CALENDAR_CLIENT_SECRET = os.environ.get('CALENDAR_CLIENT_SECRET')
CALENDAR_OAUTH_REDIRECT_URI = os.environ.get('CALENDAR_OAUTH_REDIRECT_URI')
CALENDAR_SCOPE = os.environ.get('CALENDAR_SCOPE')
GOOGLE_TOKEN_URI = os.environ.get('GOOGLE_TOKEN_URI')
