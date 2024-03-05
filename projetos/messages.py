#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
"""

from celery import shared_task

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.template import Context, Template
from django.utils import html

from users.models import Opcao
from projetos.models import Configuracao
from .models import AreaDeInteresse

from administracao.models import Carta


def render_message(template, context):
    """Recebe o nome da Carta a renderizar como texto."""
    carta = get_object_or_404(Carta, template=template)
    t = Template(carta.texto)
    message = t.render(Context(context))
    message = html.urlize(message) # Faz links de e-mail e outros links funcionarem
    return message

def htmlizar(text):
    """Coloca <br> nas quebras de linha."""
    return text.replace('\n', '<br>\n')

@shared_task
def send_mail_task(subject, message, from_email, recipient_list, **kwargs):
    send_mail(subject, message, from_email, recipient_list, **kwargs)

def email(subject, recipient_list, message, aviso_automatica=True):
    """Envia e-mail automaticamente."""
    email_from = settings.EMAIL_USER + " <" + settings.EMAIL_HOST_USER + ">"
    auth_user = settings.EMAIL_HOST_USER

    if aviso_automatica:
        configuracao = get_object_or_404(Configuracao)
        message += "<br>\n<br>\n<small style='color: gray'>"
        message += configuracao.msg_email_automatico
        message += "</small>"

    # return send_mail(subject, message, email_from, recipient_list,
    #                  fail_silently=True, auth_user=auth_user, html_message=message)

    send_mail_task.delay(subject, message, email_from, recipient_list,
                         fail_silently=True, auth_user=auth_user, html_message=message)

    return 1  # Solução temporária para manter compatibilidade

def create_message(estudante, ano, semestre):
    """Cria mensagem quando o estudante termina de preencher o formulário de seleção de propostas"""
    context_carta = {
            "estudante": estudante,
            "ano": ano,
            "semestre": semestre,
            "opcoes": Opcao.objects.filter(aluno=estudante, proposta__disponivel=True),
            "areas": AreaDeInteresse.objects.filter(area__ativa=True, area__isnull=False, usuario=estudante.user),
            "outras": AreaDeInteresse.objects.filter(area__isnull=True, usuario=estudante.user).last()
        }
    return render_message("Confirma Propostas", context_carta)

def message_reembolso(usuario, projeto, reembolso, cpf):
    """Emite mensagem de reembolso."""
    context_carta = {
        "usuario": usuario,
        "projeto": projeto,
        "reembolso": reembolso,
        "cpf": cpf,
    }
    return render_message("Mensagem de Reembolso", context_carta)

def message_agendamento(encontro, cancelado):
    """Emite menssagem de agendamento de dinâmica."""
    context_carta = {
        "encontro": encontro,
        "cancelado": cancelado,
    }
    return render_message("Agendamento de Dinâmica", context_carta)
