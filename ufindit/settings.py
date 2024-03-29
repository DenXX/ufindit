# Django settings for ufindit project.

import re

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.sqlite3',           # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME':     '/home/dsavenk/Projects/irlab/ufindit/ufindit.sqlite',                       # Or path to database file if using sqlite3.
        'USER':     '',
        'PASSWORD': '',
        'HOST':     '',                                     # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT':     '',                                     # Set to empty string for default.
    }
    if not DEBUG else {
        'ENGINE':   'django.db.backends.postgresql_psycopg2',   # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME':     'ufindit',                                  # Or path to database file if using sqlite3.
        'USER':     'ufindit',
        'PASSWORD': 'IrLabUFindItPasswd',
        'HOST':     '127.0.0.1',                                # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT':     '5432',                                     # Set to empty string for default.
    }
}

CACHES = {
    # Cache used for storing and retrieving json search results
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'ufindit_cache',
    },
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['localhost']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

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
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/home/dsavenk/Projects/irlab/ufindit/ufindit/static/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '*)m$pkyp_(rdo=3e_orqm^^^_3%r!+*gt1(5m@wkyni%q-al&^'

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
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'ufindit.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'ufindit.wsgi.application'

TEMPLATE_DIRS = (
    "/home/dsavenk/Projects/irlab/ufindit/ufindit/templates",
    "/home/dsavenk/Projects/irlab/ufindit/querydifficulty/templates",
    "/home/dsavenk/Projects/irlab/ufindit/query_url_problems/templates",
    "/home/dsavenk/Projects/irlab/ufindit/analytics/templates",
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'south',
    'httpproxy',
    'ufindit',
    'analytics',
    'querydifficulty',
    'query_url_problems',
)

AUTHENTICATION_BACKENDS = (
    'backends.EmailAuthBackend',
)

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
    
# Email settings
DEFAULT_FROM_EMAIL = 'ufindit.irlab@gmail.com'
SERVER_EMAIL = 'ufindit.irlab@gmail.com'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'ufindit.irlab@gmail.com'
EMAIL_HOST_PASSWORD = 'irlabpassword'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Application specific settings : BEGIN

SEARCH_PROXY = "bing"
RESULTS_PER_PAGE = 10
RANDOMIZE_TOPN_RESULTS = 0
FILTER_URLS = ['seoflexforum.com', 'chacha.com', 'facebook.com', 'answers.yahoo.com',
               'tipnews.info', 'wiki.answers.com']
FILTER_URLS_IF_CONTAIN_QUESTION = True

# Which SERP template to use, we can add extra html code by switching templates.
# SERP_TEMPLATE_NAME = 'query_difficulty_serp.html'
# GAME_OVER_TEMPLATE = 'survey.html'
SERP_TEMPLATE_NAME = 'serp.html'
GAME_OVER_TEMPLATE = 'game_over.html'
RULES_TEMPLATE_NAME = 'rules.html'

# dsavenk@emory.edu
BING_API_KEY = 'ua4NbbaJUUabS47ZzGM2VANoW3s+EdogrHxbtRRsg1Y'

# Amazon Mechanical Turk settings
AWS_ACCESS_KEY='1MR3K9YRD0HAV38G9B02' #'AKIAIDK22GOAOQQPMQTQ'
AWS_SECRET_ACCESS_KEY='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' #'wT4yL5RoGTd6ELx1ThM7w+xmQBx5TIj+hyeIm+De'
MTURK_REST_SANDBOX_ENDPOINT='mechanicalturk.sandbox.amazonaws.com'
MTURK_REST_ENDPOINT='mechanicalturk.amazonaws.com'

# MTURK_TASK_SUBMIT_URL= 'http://workersandbox.mturk.com/mturk/externalSubmit?'
MTURK_TASK_SUBMIT_URL= 'http://www.mturk.com/mturk/externalSubmit?'

MTURK_FRAME_HEIGHT=1200
MTURK_USONLY_REQUIREMENT=True
MTURK_HIT_LIFETIME_HOURS=72
MTURK_HIT_DURATION=1.0
MTURK_MAX_ASSIGNMENTS=20
MTURK_HIT_REWARD=1.5
MTURK_APPROVAL_DELAY=48
MTURK_APPROVED_PERCENT_REQUIREMENT=90
MTURK_MASTERS_REQUIREMENT=True
MTURK_GAME_TITLE = 'uFindIt Web Search Game'
MTURK_GAME_DESCRIPTION = 'The goal of the game is to use web search to find answers ' + \
                         'to 3 difficult questions. Please read this if HIT is not displayed ' + \
                         'http://mturkforum.com/showthread.php?10046-problem-with-hits'

# EMU settings
ENABLE_EMU_LOGGING = False

# HTTP PROXY SETTINGS
PROXY_REWRITE_RESPONSES = True
PROXY_USER_AGENT = 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'

EXTRA_RESPONSE_REWRITE_RULES = {
    '</body>':'<script type="text/javascript" src="/{task_id}/emu/emu.js"></script></body>',
} if ENABLE_EMU_LOGGING else {}

# Application specific settings : END
