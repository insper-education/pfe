#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
"""

import datetime
import subprocess
import logging

from celery import shared_task
from django.conf import settings
from django.core.management import call_command
from django.core.management import execute_from_command_line
import django.db.models.query
from django.template import Template, Context

from calendario.support import get_calendario_context

from .models import Aviso, Evento, Configuracao
from .messages import email, htmlizar

from users.models import Aluno, Professor, PFEUser

# Get an instance of a logger
logger = logging.getLogger("django")

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
        argv = ['', "mediabackup", "--compress"]
        execute_from_command_line(argv)
        return f"Backup realizado: {datetime.datetime.now()}"
    except:
        return f"Não foi possível fazer o backup: {datetime.datetime.now()}"


@shared_task
def certbot_renew():
    """Renova Certificado Digital."""
    subprocess.call(["sudo", "certbot", "renew", "--quiet"])


def avisos_do_dia():
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return None

    eventos = Evento.get_eventos(configuracao=configuracao)  # Filtra avisos do semestre

    # Checa avisos do dia
    avisos = []
    for evento in eventos:
        for aviso in Aviso.objects.filter(tipo_evento=evento.tipo_evento):
            data_evento = evento.get_data() + datetime.timedelta(days=aviso.delta)
            if data_evento == datetime.date.today():
                avisos.append(aviso)

    for aviso in avisos:

        # Preparando mensagem como template para aplicar variáveis
        subject = "Capstone | Aviso: " + aviso.titulo
        if aviso.mensagem:
            message = aviso.mensagem
        else:
            message = "Mensagem não definida."

        mensagem_como_template = Template(message)

        recipient_list = []

        if aviso.coordenacao:
            email_coordenacoes = []
            email_coordenacoes.append(str(configuracao.coordenacao.user.email))
            context = {}
            mensagem_final = mensagem_como_template.render(Context(context))
            email(subject, recipient_list + email_coordenacoes, htmlizar(mensagem_final))
            
        if aviso.operacional:
            email_operacional = []
            email_operacional.append(str(configuracao.operacao.email))
            context = {}
            mensagem_final = mensagem_como_template.render(Context(context))
            email(subject, recipient_list + email_operacional, htmlizar(mensagem_final))
                
        if aviso.comite_pfe:
            comite = PFEUser.objects.filter(membro_comite=True)
            lista_comite = [obj.email for obj in comite]
            context = {}
            mensagem_final = mensagem_como_template.render(Context(context))
            email(subject, recipient_list + lista_comite, htmlizar(mensagem_final))
                
        if aviso.todos_alunos:
            estudantes = Aluno.objects.filter(alocacao__projeto__ano=configuracao.ano, alocacao__projeto__semestre=configuracao.semestre)
            lista_estudantes = [obj.user.email for obj in estudantes]
            context = {}
            mensagem_final = mensagem_como_template.render(Context(context))
            email(subject, recipient_list + lista_estudantes, htmlizar(mensagem_final))

        if aviso.todos_orientadores:
            orientadores = Professor.objects.filter(professor_orientador__ano=configuracao.ano, professor_orientador__semestre=configuracao.semestre)
            lista_orientadores = [obj.user.email for obj in orientadores]
            context = {}
            mensagem_final = mensagem_como_template.render(Context(context))
            email(subject, recipient_list + lista_orientadores, htmlizar(mensagem_final))
            
        if aviso.contatos_nas_organizacoes:
            recipient_list += []
            context = {}
            mensagem_final = mensagem_como_template.render(Context(context))
            # email(subject, recipient_list, htmlizar(mensagem_final))  # Por enquanto, não envia para ninguém
    

def eventos_do_dia():
    # Checa eventos do calendário e envia e-mail para coordenador(es)
    context = get_calendario_context()

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return None

    for event in context:
        if context[event] and isinstance(context[event], django.db.models.query.QuerySet) and context[event].model is Evento:
            for acao in context[event]:
                if acao.startDate == datetime.date.today():

                    recipient_list = []
                    recipient_list.append(str(configuracao.coordenacao.user.email))

                    if acao.tipo_evento.sigla == "A":  # Aula
                        # Adicionando Orientadores
                        orientadores = Professor.objects.filter(professor_orientador__ano=configuracao.ano, professor_orientador__semestre=configuracao.semestre)
                        recipient_list += [obj.user.email for obj in orientadores]

                    subject = "Capstone | Evento: {0}".format(acao.get_title())
                    message = "Notificação de evento do Capstone.\n<br>"
                    message += "(mensagem informativa dos eventos do dia)\n\n<br><br>"
                    message += "<b>Evento:</b> {0}".format(acao.get_title())

                    if acao.atividade:
                        message += "<br>\n<b>Nome da Atividade:</b> {0}".format(acao.atividade)
                   
                    if acao.startDate and (acao.startDate == acao.endDate or (not acao.endDate)):
                        message += "<br>\n<b>Data:</b> {0}".format(acao.startDate.strftime("%d/%m/%Y"))
                    else:
                        message += "<br>\n<b>Data inicial:</b> {0}".format(acao.startDate.strftime("%d/%m/%Y"))
                        message += "<br>\n<b>Data final:</b> {0}".format(acao.endDate.strftime("%d/%m/%Y"))

                    if acao.location:
                        message += "<br>\n<b>Local:</b> {0}".format(acao.location)

                    if acao.descricao:
                        message += "<br>\n<b>Descrição:</b> {0}".format(acao.descricao)
                    if acao.responsavel:
                        message += "<br>\n<b>Responsável:</b> {0}".format(acao.responsavel.get_full_name())
                    if acao.observacao:
                        message += "<br>\n<b>Observações:</b> {0}".format(acao.observacao)
                    # documento (não implementado)
                    message += "<br>\n<br>\n<br>\n"

                    email(subject, recipient_list, message)


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
    