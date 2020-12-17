""""
 Desenvolvido para o Projeto Final de Engenharia
 Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
 Data: 26 de Maio de 2019
"""

import os
from celery.schedules import crontab

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '<PONHA UMA SENHA AQUI>'
# python manage.py shell -c
#  "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# SECURITY WARNING: don't run with debug turned on in production!
#DEBUG = False
DEBUG = True

ALLOWED_HOSTS = ['*']

ADMINS = [('Luciano Pereira Soares', 'lucianops@insper.edu.br'),
          ('Luciano Soares', 'lpsoares@gmail.com')]

# Application definition

INTERNAL_IPS = ['127.0.0.1', '0.0.0.0', 'localhost', "::1"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'import_export',
    'users.apps.UsersConfig',
    'projetos.apps.ProjetosConfig',
    'estudantes.apps.EstudantesConfig',
    'parceiros.apps.ParceirosConfig',
    'professores.apps.ProfessoresConfig',
    'propostas.apps.PropostasConfig',
    'django.contrib.sites',
    'dbbackup',
    #'debug_toolbar',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'pfe.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

#WSGI_APPLICATION = 'pfe.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),

        'ENGINE': 'django.db.backends.XXX',
        'NAME': 'XXX',
        'USER': 'XXX',
        'PASSWORD': 'XXX',
        'HOST': '127.0.0.1',
        'PORT': '5432',

    }

}

DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {
    "location": "../backups/backups"
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

#AUTH_PASSWORD_VALIDATORS = [
#    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
#    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
#    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
#    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
#]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
STATIC_URL = '/static/'

# Redirect to home URL after login (Default redirects to /accounts/profile/)
LOGIN_REDIRECT_URL = 'index'
#LOGOUT_REDIRECT_URL = 'logout'   #desligar, senão fica recursivo

AUTH_USER_MODEL = 'users.PFEUser'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'pfeinsper@gmail.com'
EMAIL_HOST_PASSWORD = 'XXXXXXXXX'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join('pfe.log')
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True
        },
    },
}

MEDIA_URL = '/<local_dos_arquivos>/'
MEDIA_ROOT = os.path.join(BASE_DIR, '<local_dos_arquivos>')

# CELERY
# CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_BROKER_URL = 'amqp://guest:guest@localhost//'
CELERY_BEAT_SCHEDULE = {
    'backup': {
        'task': 'projetos.tasks.backup',
        'schedule': crontab(hour=3, minute=0, day_of_week=1), # Toda segunda-feira as 3:00
    },
    "mediabackup": {
        "task": "core.tasks.mediabackup",
        "schedule": crontab(hour=3, minute=30, day_of_week=1), # Toda segunda-feira as 3:30
    },
    'send-email-daily': {
        'task': 'projetos.tasks.envia_aviso',
        'schedule': crontab(hour=6, minute=0),
    },
    'certbot-renew': {
        'task': 'projetos.tasks.certbot_renew',
        'schedule': crontab(0, 0, day_of_month='1'),
    },
}

SITE_ID = 1

SERVER = "https://pfe.insper.edu.br"

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

def show_toolbar(request):
    """Controle se exibe a barra do Debbuger."""
    return not request.is_ajax() and request.user and request.user.username == "lpsoares"
    # Só funciona o debug para mim

DEBUG_TOOLBAR_CONFIG = {
    #'SHOW_TOOLBAR_CALLBACK': lambda r: False,  # disables it
    #'SHOW_TOOLBAR_CALLBACK': 'pfe.settings.show_toolbar',
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

STATIC_ROOT = os.path.join(BASE_DIR, "static/")
