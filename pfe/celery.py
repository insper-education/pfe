"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 16 de Julho de 2020
"""

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
#from django.conf import settings
#from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pfe.settings')

APP = Celery('pfe')

#APP.conf.timezone = 'America/Sao_Paulo' #Com bug, nao funciona

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
APP.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
APP.autodiscover_tasks()
