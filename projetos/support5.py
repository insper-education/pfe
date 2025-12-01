#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 9 de Setembro de 2025
"""


import datetime
import logging

from django.template import Template, Context

from .models import Aviso, Evento, Configuracao, Projeto
from .messages import email, htmlizar

from calendario.support import get_calendario_context

from projetos.models import Banca

from users.models import Aluno, Professor, PFEUser

logger = logging.getLogger("django")  # Get an instance of a logger


def envia_mensagens_avisos(aviso_id=None, endereco=None):
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return None

    hoje = datetime.date.today()
    orientadores_ids = Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre).values_list("orientador", flat=True)
    orientadores = Professor.objects.filter(id__in=orientadores_ids)
    bancas = Banca.objects.filter(startDate__gt=hoje).order_by("startDate")
    
    estudantes = Aluno.objects.filter(alocacao__projeto__ano=configuracao.ano,
                                      alocacao__projeto__semestre=configuracao.semestre,
                                      externo__isnull=True)

    eventos = Evento.get_eventos(configuracao=configuracao)  # Filtra avisos do semestre

    # Checa avisos do dia
    avisos = []
    for evento in eventos:
        for aviso in Aviso.objects.filter(tipo_evento=evento.tipo_evento):
            if aviso_id:
                if not avisos and aviso.id == aviso_id:  # Se for um aviso específico, envia só ele
                    avisos.append([aviso, evento])
            else:  # Se não for um aviso específico, checa todos os avisos
                data_evento = evento.get_data(aviso.delta_fim) + datetime.timedelta(days=aviso.delta)
                if data_evento == datetime.date.today():
                    avisos.append([aviso, evento])

    for aviso, evento in avisos:

        # Preparando mensagem como template para aplicar variáveis
        subject = "Capstone | Aviso: " + aviso.titulo
        if aviso.mensagem:
            message = aviso.mensagem
        else:
            message = "Mensagem não definida."

        filtros = "{% load static %}{% load date_extras %}{% load eventos %}"
        mensagem_como_template = Template(filtros+message)

        context = {
                "hoje": datetime.date.today(),
                "edicao": f"{configuracao.ano}.{configuracao.semestre}",
                "delta": aviso.delta,
                "delta_invert": -aviso.delta,
                "delta_fim": aviso.delta_fim,
                "evento": evento,
                "eventos": eventos,
                "orientadores": orientadores,
                "estudantes": estudantes,
                "bancas": bancas,
            }

        mensagem_final = mensagem_como_template.render(Context(context))

        recipient_list = []

        mensagem_enviados = "Aviso enviado para: "
        if aviso.coordenacao:
            mensagem_enviados += "[<b>Coordenação</b>], "
        if aviso.operacional:
            mensagem_enviados += "[<b>Operacional</b>], "
        if aviso.comite:
            mensagem_enviados += "[<b>Comitê</b>], "
        if aviso.todos_alunos:
            mensagem_enviados += "[<b>Estudantes</b>], "
        if aviso.todos_orientadores:
            mensagem_enviados += "[<b>Orientadores</b>], "
        if aviso.contatos_nas_organizacoes:
            mensagem_enviados += "[<b>Contatos nas Organizações</b>], "
        mensagem_enviados = mensagem_enviados[:-2] + "<br><hr><br>"

        if endereco:  # Se for um endereço específico, envia só para ele
            recipient_list.append(endereco)
            email(subject, recipient_list, htmlizar(mensagem_enviados + mensagem_final))

        else:  # Senão, envia para os grupos selecionados

            if aviso.coordenacao:
                email_coordenacoes = []
                email_coordenacoes.append(str(configuracao.coordenacao.user.email))
                email(subject, recipient_list + email_coordenacoes, htmlizar(mensagem_enviados + mensagem_final))
                
            if aviso.operacional:
                email_operacional = []
                email_operacional.append(str(configuracao.operacao.email))
                email(subject, recipient_list + email_operacional, htmlizar(mensagem_enviados + mensagem_final))
                    
            if aviso.comite:
                comite = PFEUser.objects.filter(membro_comite=True)
                lista_comite = [obj.email for obj in comite]
                email(subject, recipient_list + lista_comite, htmlizar(mensagem_final))
                    
            if aviso.todos_alunos:
                estudantes = Aluno.objects.filter(alocacao__projeto__ano=configuracao.ano, 
                                                alocacao__projeto__semestre=configuracao.semestre, 
                                                externo__isnull=True)
                lista_estudantes = [obj.user.email for obj in estudantes]
                email(subject, recipient_list + lista_estudantes, htmlizar(mensagem_final))

            if aviso.todos_orientadores:
                orientadores = Professor.objects.filter(professor_orientador__ano=configuracao.ano, professor_orientador__semestre=configuracao.semestre)
                lista_orientadores = [obj.user.email for obj in orientadores]
                email(subject, recipient_list + lista_orientadores, htmlizar(mensagem_final))
                
            if aviso.contatos_nas_organizacoes:
                recipient_list += []
                # email(subject, recipient_list, htmlizar(mensagem_final))  # Por enquanto, não envia para ninguém


def envia_mensagens_eventos():
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return None
    
    # Coletando todos os eventos possíveis
    context = get_calendario_context()
    eventos = context["eventos_academicos"]
    eventos["coordenacao"] = context["coordenacao"]

    for event in eventos:
        for acao in eventos[event]:
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