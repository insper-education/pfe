""""
 Desenvolvido para o Projeto Final de Engenharia
 Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
 Data: 26 de Maio de 2019
"""

import os
import logging
from celery.schedules import crontab


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "<PONHA UMA SENHA AQUI>"
# python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

ADMINS = [("Luciano Pereira Soares", "lucianops@insper.edu.br"), 
          ("Luciano Soares", "lpsoares@gmail.com")]

INTERNAL_IPS = ["127.0.0.1", "0.0.0.0", "localhost", "::1"]

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
    'organizacoes.apps.OrganizacoesConfig',
    'professores.apps.ProfessoresConfig',
    'propostas.apps.PropostasConfig',
    'documentos.apps.DocumentosConfig',
    'administracao.apps.AdministracaoConfig',
    'operacional.apps.OperacionalConfig',
    'calendario.apps.CalendarioConfig',
    'academica.apps.AcademicaConfig',
    'coordenacao.apps.CoordenacaoConfig',
    'django.contrib.sites',
    'dbbackup',
    'axes',
    'log_viewer',
    #'debug_toolbar',
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'pfe.middleware.MaintenanceModeMiddleware',
    'axes.middleware.AxesMiddleware',
    'pfe.timing_middleware.TimingMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Sistema de bloqueio de acesso
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 3  # 3 tentativas

# Libera usuário depois de uma hora
AXES_COOLOFF_TIME = 1 # 1 hour

# Prevent login from IP under a particular username if the attempt limit has been exceeded,
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760

ROOT_URLCONF = "pfe.urls"

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

BACKUP_CLEANUP_DAYS = 365
BACKUP_FOLDER = "../backups/backups"

DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": BACKUP_FOLDER}
DBBACKUP_CONNECTORS = {
    'default': {
        'CONNECTOR': 'dbbackup.db.postgresql.PgDumpBinaryConnector',
        'DROP': True,
        'SINGLE_TRANSACTION': False
    }
}

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_L10N = True
USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
STATIC_URL = "/static/"

# Redirect to home URL after login (Default redirects to /accounts/profile/)
LOGIN_REDIRECT_URL = "index"

AUTH_USER_MODEL = "users.PFEUser"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_PORT = 587
EMAIL_HOST_USER = "exemplo@mail.com"
EMAIL_HOST_PASSWORD = "XXXXXXXXX"
EMAIL_USER = "PFE Insper"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

class TimingFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, "duration"):
            record.message = f"{record.message} | Time taken: {record.duration:.2f} seconds"
        return super().format(record)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            '()': TimingFormatter,
            'format': '[{levelname}] ({asctime}) |{module}|: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join('pfe.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True
        },
    },
}

LOG_VIEWER_FILES = ["pfe",]
LOG_VIEWER_FILES_PATTERN = "*.log*"
LOG_VIEWER_FILES_DIR = "logs/"
LOG_VIEWER_PAGE_LENGTH = 25       # total log lines per-page
LOG_VIEWER_MAX_READ_LINES = 1000  # total log lines will be read
LOG_VIEWER_FILE_LIST_MAX_ITEMS_PER_PAGE = 25 # Max log files loaded in Datatable per page
LOG_VIEWER_PATTERNS = ['[INFO]', '[DEBUG]', '[WARNING]', '[ERROR]', '[CRITICAL]']
LOG_VIEWER_EXCLUDE_TEXT_PATTERN = None  # String regex expression to exclude the log from line

MEDIA_URL = '/<local_dos_arquivos>/'
MEDIA_ROOT = os.path.join(BASE_DIR, '<local_dos_arquivos>')
FILE_UPLOAD_PERMISSIONS = 0o644

GITHUB_USERNAME = "<NOME_USUARIO_GITHUB>"
GITHUB_TOKEN = "<SEU_TOKEN_GITHUB>"

# CELERY
# Tempo usado para os alarmes eh GMT
CELERY_BROKER_URL = 'amqp://guest:guest@localhost//'
CELERY_BEAT_SCHEDULE = {
    "backup": {
        "task": "projetos.tasks.backup",
        "schedule": crontab(minute=0, hour=0, day_of_month='1'),
    },
    "mediabackup": {
        "task": "core.tasks.mediabackup",
        "schedule": crontab(minute=0, hour=0, day_of_month='1'),
    },
    "remove_old_backups": {
        "task": "projetos.tasks.remove_old_backups",
        "schedule": crontab(minute=0, hour=0, day_of_week='1'),
    },
    "send-email-daily": {
        "task": "projetos.tasks.envia_aviso",
        "schedule": crontab(minute=0, hour=10),
    },
    "certbot-renew": {
        "task": "projetos.tasks.certbot_renew",
        "schedule": crontab(minute=0, hour=0, day_of_month='1'),
    },
    'apaga_tmp': {
        'task': 'projetos.tasks.apaga_tmp',
        'schedule': crontab(minute=0, hour=0, day_of_week=2),
    },
    'decontos': {
        'task': 'projetos.tasks.decontos',
        'schedule': crontab(hour=5, minute=10),
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
    # Só funciona em debug

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

STATIC_ROOT = os.path.join(BASE_DIR, "static/")

SALT = "pfe"

MAINTENANCE_MODE = int(os.environ.get("MAINTENANCE_MODE", 0))

ADMIN_SITE = "admin/"

CONTATO = "por favor contactar: <a href='mailto:xxxx@insper.edu.br'>xxxx@insper.edu.br</a>"
