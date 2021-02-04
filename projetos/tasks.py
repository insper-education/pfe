#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
"""

import datetime
import subprocess
from celery import task
from celery import shared_task
from django.conf import settings
from django.core.management import call_command

from calendario.views import get_calendario_context

from .models import Aviso
from .messages import email, htmlizar


@shared_task
def backup():
    """Rotina de Backup."""
    if settings.DEBUG is True:
        return "Não se pode fazer o Backup: Debug está True"

    try:
        call_command("dbbackup")
        return f"Backup realizado: {datetime.datetime.now()}"
    except:
        return f"Não foi possível fazer o backup: {datetime.datetime.now()}"


@shared_task
def mediabackup():
    """Rotina de Backup dos arquivos (media)."""
    if settings.DEBUG is True:
        return "Não pode fazer o Backup: Debug está True"

    try:
        call_command("mediabackup")
        return f"Backup realizado: {datetime.datetime.now()}"
    except:
        return f"Não foi possível fazer o backup: {datetime.datetime.now()}"


@task
def certbot_renew():
    """Renova Certificado Digital."""
    subprocess.call(['sudo', 'certbot', 'renew', '--quiet'])


@task
def envia_aviso():
    """Gera um aviso por e-mail."""
    avisos = []
    for aviso in Aviso.objects.all():
        if aviso.get_data() == datetime.date.today():
            avisos.append(aviso)

    recipient_list = ['pfeinsper@gmail.com', 'lpsoares@insper.edu.br', ]
    for aviso in avisos:
        subject = 'Aviso: '+aviso.titulo
        if aviso.mensagem:
            message = aviso.mensagem
        else:
            message = "Mensagem não definida."
        verify = email(subject, recipient_list, htmlizar(message))
        if verify != 1:
            # print("Algum problema de conexão, contacte: lpsoares@insper.edu.br")
            pass

    # Eventos do calendário
    context = get_calendario_context()
    for event in context:
        for acao in context[event]:
            if acao.startDate == datetime.date.today():
                subject = "PFE {0} : {1}".format(event, acao.get_title())
                message = "{0} : {1}".format(event, acao.get_title())
                message += "<br>\nLocal : {0}".format(acao.location)
                if acao.startDate == acao.endDate:
                    message += "<br>\ndata = {0}".format(acao.startDate)
                else:
                    message += "<br>\ndata inicial = {0}".format(acao.startDate)
                    message += "<br>\ndata final = {0}".format(acao.endDate)
                verify = email(subject, recipient_list, message)
                if verify != 1:
                    # print("Algum problema de conexão, contacte: lpsoares@insper.edu.br")
                    pass
