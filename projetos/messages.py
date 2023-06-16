#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
"""

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.template import Context, Template
from django.utils import html

from users.models import Opcao
from .models import AreaDeInteresse
#from .models import Area

from administracao.models import Carta


def htmlizar(text):
    """Coloca <br> nas quebras de linha."""
    return text.replace('\n', '<br>\n')

def email(subject, recipient_list, message):
    """Envia um e-mail para o HOST_USER."""
    email_from = settings.EMAIL_USER + " <" + settings.EMAIL_HOST_USER + ">"
    auth_user = settings.EMAIL_HOST_USER
    return send_mail(subject, message, email_from, recipient_list,
                     fail_silently=True, auth_user=auth_user, html_message=message)

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
    carta = get_object_or_404(Carta, template="Confirma Propostas")
    t = Template(carta.texto)
    message = t.render(Context(context_carta))
    message = html.urlize(message) # Faz links de e-mail, outros sites funcionarem
    return message

def message_reembolso(usuario, projeto, reembolso, cpf):
    """Emite menssagem de reembolso."""
    message = '<br>\n'
    message += '&nbsp;&nbsp;Caro <b>Dept. de Carreiras</b>\n\n'
    message += '<br><br>\n\n'
    message += '&nbsp;&nbsp;Por favor, encaminhem o pedido de reembolso de: '
    message += usuario.first_name+" "+usuario.last_name+" ("+usuario.username+')<br>\n'
    message += '&nbsp;&nbsp;CPF: '+cpf[:3]+'.'+cpf[3:6]+'.'+cpf[6:9]+'-'+cpf[9:11]+'<br>\n'
    # if usuario.aluno.curso == "C":
    #     curso = "Computação"
    # elif usuario.aluno.curso == "M":
    #     curso = "Mecânica"
    # else:
    #     curso = "Mecatrônica"
    curso = str(usuario.aluno.curso2)
    message += '&nbsp;&nbsp;Curso: '+curso+'<br>\n'
    if projeto:
        message += '<br>\n'
        message += '&nbsp;&nbsp;Participante do projeto: '+projeto.titulo+'<br>\n'
    message += '<br>\n'
    message += '&nbsp;&nbsp;Descrição: '+reembolso.descricao+'<br>\n'
    message += '<br>\n'
    message += '&nbsp;&nbsp;Banco: '
    message += reembolso.banco.nome+' ('+str(reembolso.banco.codigo)+')'+'<br>\n'
    message += '&nbsp;&nbsp;Conta: ' + reembolso.conta+'<br>\n'
    message += '&nbsp;&nbsp;Agência: ' + reembolso.agencia+'<br>\n'
    message += '<br>\n'
    message += '&nbsp;&nbsp;Valor do reembolso: ' + reembolso.valor+'<br>\n'
    message += '<br>\n'
    message += '<br>\n'
    message += '&nbsp;&nbsp;Para isso use o Centro de Custo: '
    message += '200048 - PROJETO FINAL DE ENGENHARIA<br>\n'
    message += '&nbsp;&nbsp;Com a conta contábil: '
    message += '400339 - INSUMOS PARA EQUIPAMENTOS DOS LABORATÓRIOS<br>\n'
    message += '<br>\n'+("&nbsp;"*12)+"atenciosamente, coordenação do PFE"
    message += '&nbsp;<br>\n'
    message += '&nbsp;<br>\n'
    message += '&nbsp;&nbsp;&nbsp;Obs: você deverá entregar todas as notas fiscais originais, '
    message += 'ou senão imprimir, diretamente no departamento de carreiras,'
    message += 'sem isso o processo não avançará.<br>\n'

    return message

def message_agendamento(encontro, cancelado):
    """Emite menssagem de agendamento de dinâmica."""
    message = '<br>\n'
    message += '&nbsp;&nbsp;Grupo do Projeto <b>'
    message += str(encontro.projeto)
    message += '</b>\n\n'
    message += '<br><br>\n\n'
    message += '&nbsp;&nbsp;Marcada dinâmica do PFE: '
    message += 'dia ' + str(encontro.startDate.strftime("%d/%m/%Y")) + ' das ' + str(encontro.startDate.strftime("%H:%M")) + ' às ' + str(encontro.endDate.strftime("%H:%M"))
    message += '<br>\n'
    if encontro.location:
        message += '&nbsp;&nbsp;Local: '
        message += str(encontro.location)
        message += '<br>\n'
    if encontro.facilitador:
        message += '&nbsp;&nbsp;Com: '
        message += str(encontro.facilitador)
        message += '<br>\n'

    if cancelado:
        message += '<br>\n'
        message += '&nbsp;&nbsp;<font color="red">Obs: horário previamente agendado ' + cancelado + ' foi cancelado.</font><br>\n'
        message += '<br>\n'

    return message
