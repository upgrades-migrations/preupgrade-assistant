# Django settings for webui project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('root', 'root@localhost'),
)

MANAGERS = ADMINS

import os

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = PROJECT_DIR

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DATA_DIR, 'db.sqlite'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*', ]

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
# oscap dont provide TZ aware dates anyway
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(DATA_DIR, 'upload')

RESULTS_DIR = os.path.join(DATA_DIR, 'results')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ttw*yd&#$n1)=!2_w+q*)#h1!i0srh=z1%51&ezf)-kny@7%w3'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'auth.auth_middleware.CustomAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

LOGIN_URL = 'auth-login'
LOGIN_EXEMPT_URLS = ['^xmlrpc/', '^submit/', '^login/', '^admin/', '^first/']

ROOT_URLCONF = 'webui.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'webui.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates')
)

#INTERNAL_IPS = ('127.0.0.1', '127.0.0.1:8000',)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'report',
    'config',
    'xmlrpc_backend',
    'south',
]

if DEBUG:
    opt_apps = ['django_extensions', 'debug_toolbar']
    for mod in opt_apps:
        try:
            __import__(mod)
        except ImportError:
            pass
        else:
            INSTALLED_APPS.append(mod)

XMLRPC_METHODS = {
    'submission': (
        ('xmlrpc.submission', 'submit'),
    ),
}

def get_log_file():
    if DEBUG:
        return '/var/tmp/preupgrade-ui.log'
    else:
        return '/var/log/preupgrade/ui.log'

LOGGING_CONFIG = None
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        # dont mail admins where there is an error
        # 'mail_admins': {
        #     'level': 'ERROR',
        #     'filters': ['require_debug_false'],
        #     'class': 'django.utils.log.AdminEmailHandler'
        # },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/var/log/preupgrade/ui.log',
            'maxBytes': 10 * (1024 ** 2),  # 10 MB
            'backupCount': 7,
        },
    },
    'loggers': {
        #'django.request': {
        #    'handlers': ['mail_admins'],
        #    'level': 'ERROR',
        #    'propagate': True,
        #},
        'preup_ui': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}
