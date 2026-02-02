#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
"""

import os
import time
import datetime
import subprocess
import logging

from celery import shared_task
from django.conf import settings
from django.core.management import call_command
from django.core.management import execute_from_command_line

from .support5 import envia_mensagens_avisos, envia_mensagens_eventos

from academica.support import lanca_descontos

# Ensure shared tasks defined outside tasks.py are registered by Celery autodiscovery
from .messages import send_mail_task  # noqa: F401

logger = logging.getLogger("django")  # Get an instance of a logger


@shared_task
def backup():
    """Rotina de Backup."""
    if settings.DEBUG:
        msg = "Não se pode fazer o Backup: Debug está True"
        logger.warning(msg)
        return msg

    try:
        call_command("dbbackup")
        msg = f"Backup realizado: {datetime.datetime.now()}"
        logger.info(msg)
        return msg
    except Exception as e:
        msg = f"Não foi possível fazer o backup: {datetime.datetime.now()} | Erro: {str(e)}"
        logger.error(msg)
        return msg


@shared_task
def mediabackup():
    """Rotina de Backup dos arquivos (media)."""
    if settings.DEBUG:
        msg = "Não pode fazer o Backup: Debug está True"
        logger.warning(msg)
        return msg

    try:
        argv = ['', "mediabackup", "--compress"]
        execute_from_command_line(argv)
        msg = f"Backup realizado: {datetime.datetime.now()}"
        logger.info(msg)
        return msg
    except Exception as e:
        msg = f"Não foi possível fazer o backup: {datetime.datetime.now()} | Erro: {str(e)}"
        logger.error(msg)
        return msg


@shared_task
def remove_old_backups():
    """Remove backups mais velhos que o número de dias em um dado diretório."""
    days = settings.BACKUP_CLEANUP_DAYS
    backup_dir = settings.BACKUP_FOLDER

    now = time.time()
    cutoff = now - days * 86400  # 60 days in seconds

    if not os.path.isdir(backup_dir):
        msg = f"Diretório de Backup: {backup_dir}, não existe."
        logger.error(msg)
        return msg

    removed = 0
    for filename in os.listdir(backup_dir):
        file_path = os.path.join(backup_dir, filename)
        if os.path.isfile(file_path):
            file_mtime = os.path.getmtime(file_path)
            if file_mtime < cutoff:
                try:
                    os.remove(file_path)
                    removed += 1
                    logger.warning(f"Removido backup antigo: {file_path}")
                except Exception as e:
                    logger.error(f"Erro ao remover {file_path}: {str(e)}")
    msg = f"Removidos {removed} backups antigos de mais de {days} dias do diretório: {backup_dir}"
    logger.warning(msg)
    return msg


@shared_task
def certbot_renew():
    """Renova Certificado Digital."""
    subprocess.call(["sudo", "certbot", "renew", "--quiet"])


def avisos_do_dia():
    """Envia avisos do dia por e-mail."""
    envia_mensagens_avisos()


def eventos_do_dia():
    """Checa eventos do calendário e envia e-mail para coordenador(es)"""
    envia_mensagens_eventos()


@shared_task
def envia_aviso():
    """Envia avisos por e-mail."""
    avisos_do_dia()
    eventos_do_dia()


@shared_task
def apaga_tmp():
    """Rotina que apaga quaisquer arquivos que esteja na pasta 'tmp'."""
    pasta_tmp = settings.MEDIA_ROOT + "/tmp"
    subprocess.call(f"sudo rm -rf {pasta_tmp}/*", shell=True)


@shared_task
def decontos():
    """Calcula descontos para estudantes do semestre."""
    lanca_descontos()
