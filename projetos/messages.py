#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
"""

from celery import shared_task
#from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.template import Context, Template
from django.utils import html
#from django.utils.html import urlize

from users.models import Opcao
from projetos.models import Configuracao, Projeto, Banca, Certificado

from .models import AreaDeInteresse

from administracao.models import Carta

logger = logging.getLogger("django")  # Para marcar mensagens de log

def render_message(template, context, urlize=True):
    """Recebe o nome da Carta a renderizar como texto."""
    carta = get_object_or_404(Carta, template=template)
    t = Template(carta.texto)
    message = t.render(Context(context))
    if urlize:
        message = html.urlize(message) # Faz links de e-mail e outros links funcionarem
    return message

def htmlizar(text):
    """Coloca <br> nas quebras de linha e manter espaços."""
    text = text.replace("\n", "<br>\n")
    text = text.replace("  ", "&nbsp; ")
    #text = urlize(text, nofollow=True) #Como algumas mensagens estão com links, o urlize bagunça o texto

    return text

@shared_task
def send_mail_task(subject, message, from_email, recipient_list, **kwargs):
    send_mail(subject, message, from_email, recipient_list, **kwargs)

def email(subject, recipient_list, message, aviso_automatica=True, delay_seconds=0):
    """Envia e-mail automaticamente (ou com atraso)."""
    email_from = settings.EMAIL_USER + " <" + settings.EMAIL_HOST_USER + ">"
    auth_user = settings.EMAIL_HOST_USER

    if aviso_automatica:
        configuracao = get_object_or_404(Configuracao)
        message += "<br>\n<br>\n<small style='color: gray'>"
        message += configuracao.msg_email_automatico
        message += "</small>"

    # Removing "\\r\\n' from header 'Subject' to avoid breaking the email
    subject = subject.replace('\r', '').replace('\n', '')
    
    try:
        if delay_seconds == 0:
            # Envia e-mail imediatamente
            send_mail_task.delay(subject, message, email_from, recipient_list,
                                fail_silently=True, auth_user=auth_user, html_message=message)
        else:
            # Agenda tarefa para enviar e-mail com possibilidade de atraso
            send_mail_task.apply_async(
                args=[subject, message, email_from, recipient_list],
                kwargs={"fail_silently": True, "auth_user": auth_user, "html_message": message},
                countdown=delay_seconds
            )

    except Exception as e:
        error_message = "Problema no envio de e-mail, subject=" + subject + ", message=" + message + ", recipient_list=" + str(recipient_list) + ", error=" + str(e)
        logger.error(error_message)


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

def message_agendamento_dinamica(encontro, cancelado):
    """Emite menssagem de agendamento de dinâmica."""
    context_carta = {
        "encontro": encontro,
        "cancelado": cancelado,
    }
    return render_message("Agendamento de Dinâmica", context_carta)

def message_cancelamento(encontro):
    """Emite menssagem de cancelamento de agendamento de dinâmica."""
    context_carta = {
        "encontro": encontro,
    }
    return render_message("Cancelamento de Dinâmica", context_carta)


def prepara_mensagem_email(request, tipo, primarykey):
    
    if tipo == "banca":
    
        banca = get_object_or_404(Banca, pk=primarykey)
        projeto = banca.get_projeto()

        para = ""
        if banca:
            for membro in banca.membros():
                para += membro.get_full_name() + " <" + membro.email + ">; "
                
        if banca and banca.alocacao:
            subject = "Capstone | Banca: " + banca.alocacao.aluno.user.get_full_name() + " " + banca.alocacao.projeto.get_titulo_org()
        else:
            subject = "Capstone | Banca: " + projeto.get_titulo_org()
        
        context_carta = {
            "request": request,
            "projeto": projeto,
            "banca": banca,
        }
        message = render_message("Mensagem Banca", context_carta)

    #### NÃO PARECE FAZER SENTIDO ENVIAR MENSAGEM PARA UMA BANCA DE PROJETO SEM TER UMA BANCA ####
    # if tipo == "banca_projeto":
    
    #     projeto = get_object_or_404(Projeto, pk=primarykey)
    #     banca = None

    #     para = ""
    #     if banca.composicao.exame.sigla in ["BI", "BF"]:  # Interm ou Final
    #         if projeto and projeto.orientador:
    #             para += projeto.orientador.user.get_full_name() + " <" + projeto.orientador.user.email + ">; "
    #             for coorientador in projeto.coorientador_set.all():
    #                 para += coorientador.usuario.get_full_name() + " <" + coorientador.usuario.email + ">; "
    #     if banca:
    #         for membro in banca.membros():
    #             para += membro.get_full_name() + " <" + membro.email + ">; "
        
    #     if banca and banca.alocacao:
    #         subject = "Capstone | Banca: " + banca.alocacao.aluno.user.get_full_name() + " [" + banca.alocacao.projeto.organizacao.nome + "] " +  banca.alocacao.projeto.get_titulo()
    #     else:
    #         subject = "Capstone | Banca: [" + projeto.organizacao.nome + "] " +  projeto.get_titulo()
        
    #     context_carta = {
    #         "request": request,
    #         "projeto": projeto,
    #     }
    #     message = render_message("Mensagem Banca", context_carta)

    elif tipo == "certificado":
    
        certificado = get_object_or_404(Certificado, pk=primarykey)
        configuracao = get_object_or_404(Configuracao)

        para = ""
        if certificado.usuario:
            para += certificado.usuario.get_full_name() + " <" + certificado.usuario.email + ">"

        subject = "Capstone | Certificado: " + certificado.tipo_certificado.titulo
        
        context_carta = {
            "request": request,
            "configuracao": configuracao,
            "certificado": certificado,
        }
        message = render_message("Mensagem Certificado", context_carta)

    para = para.strip()
    if para[-1] == ";":
        para = para[:-1]  # tirando o ultimo ";"

    return subject, para, message

