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
from django.core.management import execute_from_command_line
import django.db.models.query

from calendario.views import get_calendario_context

from .models import Aviso, Evento, Configuracao
from .messages import email, htmlizar

from users.models import Aluno, Professor, PFEUser

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
        # call_command("mediabackup")
        argv = ['', 'mediabackup', '--compress']
        execute_from_command_line(argv)
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
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return None

    # Checa avisos do dia e envia e-mail para coordenação
    eventos = Evento.objects.filter(startDate__year=configuracao.ano)
    if configuracao.semestre == 1:
        eventos = eventos.filter(startDate__month__lt=7)
    else:
        eventos = eventos.filter(startDate__month__gt=6)

    # Checa avisos do dia e envia e-mail para coordenação
    avisos = []
    for evento in eventos:
        for aviso in Aviso.objects.filter(tipo_de_evento=evento.tipo_de_evento):
            data_evento = evento.get_data() + datetime.timedelta(days=aviso.delta)
            if data_evento == datetime.date.today():
                avisos.append(aviso)

    for aviso in avisos:

        recipient_list = ['pfeinsper@gmail.com', ]

        if aviso.coordenacao:
            coordenacoes = PFEUser.objects.filter(coordenacao=True)
            email_coordenacoes = []
            for coordenador in coordenacoes:
                email_coordenacoes.append(str(coordenador.email))
            recipient_list += email_coordenacoes
        if aviso.comite_pfe:
            comite = PFEUser.objects.filter(membro_comite=True)
            lista_comite = [obj.email for obj in comite]
            recipient_list += lista_comite
        if aviso.todos_alunos:
            estudantes = Aluno.objects.filter(alocacao__projeto__ano=configuracao.ano, alocacao__projeto__semestre=configuracao.semestre)
            lista_estudantes = [obj.user.email for obj in estudantes]
            recipient_list += lista_estudantes
        if aviso.todos_orientadores:
            orientadores = Professor.objects.filter(professor_orientador__ano=configuracao.ano, professor_orientador__semestre=configuracao.semestre)
            lista_orientadores = [obj.user.email for obj in orientadores]
            recipient_list += lista_orientadores
        if aviso.contatos_nas_organizacoes:
            recipient_list += []

        subject = 'Aviso: ' + aviso.titulo
        if aviso.mensagem:
            message = aviso.mensagem
        else:
            message = "Mensagem não definida."
        verify = email(subject, recipient_list, htmlizar(message))
        if verify != 1:
            # Algum problema de conexão, contacte: lpsoares@insper.edu.br
            pass

    # Checa eventos do calendário e envia e-mail para destinatário
    context = get_calendario_context()

    #recipient_list = ['pfeinsper@gmail.com', 'lpsoares@insper.edu.br',]  # Soh manda para coordenação
    coordenacoes = PFEUser.objects.filter(coordenacao=True)
    recipient_list = []
    for coordenador in coordenacoes:
        recipient_list.append(str(coordenador.email))

    for event in context:
        if context[event] and isinstance(context[event], django.db.models.query.QuerySet) and context[event].model is Evento:
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
                        # Algum problema de conexão, contacte: lpsoares@insper.edu.br
                        pass
