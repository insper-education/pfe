#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
"""

from celery import shared_task
#from datetime import datetime, timedelta
import logging
from email.utils import parseaddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404
from django.template import Context, Template
from django.utils import html
from django.utils.html import strip_tags

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
    
    if carta.texto_en:
        t_en = Template(carta.texto_en)
        message_en = t_en.render(Context(context))
        message = f"{message}\n<hr style='margin: 2em 0; border: 1px solid #ddd;'>\n{message_en}"

    if urlize:
        message = html.urlize(message) # Faz links de e-mail e outros links funcionarem
    return message

def htmlizar(text):
    """Converte texto simples para HTML preservando quebras e espaçamento."""
    if text is None:
        return ""

    text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = html.escape(text)
    text = text.replace("\n", "<br>\n")
    while "  " in text:
        text = text.replace("  ", "&nbsp; ")
    return text


def _coerce_addresses(value):
    """Normaliza entradas de e-mail para lista de strings."""
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = [value]

    addresses = []
    for item in raw_items:
        if item is None:
            continue

        text = str(item).strip()
        if not text:
            continue

        for part in text.replace(";", ",").split(","):
            part = part.strip()
            if part:
                addresses.append(part)

    return addresses


def _split_valid_addresses(addresses):
    """Separa enderecos validos dos invalidos."""
    valid = []
    invalid = []

    for address in addresses:
        _, parsed_email = parseaddr(address)
        candidate = (parsed_email or address or "").strip()

        try:
            validate_email(candidate)
            valid.append(candidate)
        except ValidationError:
            invalid.append(address)

    return valid, invalid

@shared_task
def send_mail_task(subject, message, from_email, recipient_list, **kwargs):
    calendar_invite = kwargs.pop("calendar_invite", None)
    reply_to = kwargs.pop("reply_to", None)

    html_message = kwargs.pop("html_message", None)
    fail_silently = kwargs.pop("fail_silently", True)
    auth_user = kwargs.pop("auth_user", None)

    subject = str(subject or "")
    message = str(message or "")
    html_message = str(html_message) if html_message is not None else None

    # Preserva o HTML original do corpo mesmo quando html_message nao e enviado explicitamente.
    html_content = html_message if html_message is not None else message
    plain_content = strip_tags(message)

    recipients = _coerce_addresses(recipient_list)
    valid_recipients, invalid_recipients = _split_valid_addresses(recipients)
    if invalid_recipients:
        logger.warning("Destinatarios invalidos ignorados: %s", invalid_recipients)

    if not valid_recipients:
        logger.error("Nenhum destinatario valido para envio. subject=%s", subject)
        return {"sent": 0, "failed": [], "invalid": invalid_recipients}

    normalized_reply_to = _coerce_addresses(reply_to)
    valid_reply_to, invalid_reply_to = _split_valid_addresses(normalized_reply_to)
    if invalid_reply_to:
        logger.warning("Reply-To invalido ignorado: %s", invalid_reply_to)

    try:
        if auth_user:
            connection = get_connection(username=auth_user, password=settings.EMAIL_HOST_PASSWORD)
        else:
            connection = get_connection()
    except Exception as e:
        logger.exception("Falha ao criar conexao de e-mail. subject=%s, error=%s", subject, str(e))
        if fail_silently:
            return {
                "sent": 0,
                "failed": [{"reason": "connection_error", "error": str(e)}],
                "invalid": invalid_recipients,
                "invalid_reply_to": invalid_reply_to,
            }
        raise

    try:
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=html_content or plain_content,
            from_email=from_email,
            to=valid_recipients,
            reply_to=valid_reply_to or None,
            connection=connection,
        )

        if html_content:
            # Outlook tende a respeitar melhor quando o corpo principal ja e text/html.
            email_message.content_subtype = "html"

        if calendar_invite:
            method = calendar_invite.get("method", "REQUEST")
            content = calendar_invite.get("content", "")
            filename = calendar_invite.get("filename", "invite.ics")
            email_message.attach(filename, content, f"text/calendar; method={method}; charset=UTF-8")

        sent_count = email_message.send(fail_silently=fail_silently)

        return {
            "sent": sent_count,
            "failed": [],
            "invalid": invalid_recipients,
            "invalid_reply_to": invalid_reply_to,
        }

    except Exception as e:
        logger.exception("Falha no envio de e-mail. subject=%s, error=%s", subject, str(e))
        if fail_silently:
            return {
                "sent": 0,
                "failed": [{"reason": "send_error", "error": str(e)}],
                "invalid": invalid_recipients,
                "invalid_reply_to": invalid_reply_to,
            }
        raise

def email(subject, recipient_list, message, aviso_automatica=True, delay_seconds=0, calendar_invite=None, reply_to=None):
    """Envia e-mail automaticamente (ou com atraso)."""
    email_from = settings.EMAIL_USER + " <" + settings.EMAIL_HOST_USER + ">"
    auth_user = settings.EMAIL_HOST_USER

    if aviso_automatica:
        configuracao = get_object_or_404(Configuracao)
        message += "<br>\n<br>\n<small style='color: gray; line-height: 1.0;'>"
        message += configuracao.msg_email_automatico
        message += "</small>"

    # Removing "\\r\\n" from header "Subject" to avoid breaking the email
    subject = str(subject or "").replace("\r", "").replace("\n", "")
    
    try:
        if delay_seconds == 0:
            # Envia e-mail imediatamente
            send_mail_task.delay(subject, message, email_from, recipient_list,
                                fail_silently=True, auth_user=auth_user, html_message=message,
                                calendar_invite=calendar_invite, reply_to=reply_to)
        else:
            # Agenda tarefa para enviar e-mail com possibilidade de atraso
            send_mail_task.apply_async(
                args=[subject, message, email_from, recipient_list],
                kwargs={
                    "fail_silently": True,
                    "auth_user": auth_user,
                    "html_message": message,
                    "calendar_invite": calendar_invite,
                    "reply_to": reply_to,
                },
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
    carta = render_message("Agendamento de Dinâmica", context_carta, urlize=False)
    return carta

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

        message = render_message("Mensagem Banca", context_carta, urlize=False)

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

