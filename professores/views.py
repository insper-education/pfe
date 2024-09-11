#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import os
import datetime
import dateutil.parser
import logging

from urllib.parse import quote, unquote

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import html

from users.models import PFEUser, Professor, Aluno, Alocacao
from users.support import get_edicoes

from projetos.models import Coorientador, ObjetivosDeAprendizagem, Avaliacao2, Observacao
from projetos.models import Banca, Evento, Encontro, Documento, Certificado
from projetos.models import Projeto, Configuracao, Organizacao
from projetos.support import converte_letra, converte_conceito
from projetos.support import get_objetivos_atuais
from projetos.messages import email, render_message, htmlizar
from projetos.arquivos import le_arquivo

from academica.models import Exame, Composicao, Peso

from .support import professores_membros_bancas, falconi_membros_banca
from .support import editar_banca
from .support import recupera_orientadores_por_semestre
from .support import recupera_coorientadores_por_semestre
from .support import move_avaliacoes
from .support import converte_conceitos, arredonda_conceitos

from estudantes.models import Relato, Pares

from academica.support import filtra_composicoes, filtra_entregas

from documentos.models import TipoDocumento

from administracao.support import usuario_sem_acesso

# Get an instance of a logger
logger = logging.getLogger(__name__)

def get_evento(evento_id, configuracao):
    if configuracao.semestre == 1:
        eventos = Evento.objects.filter(tipo_de_evento=evento_id, endDate__year=configuracao.ano, endDate__month__lt=7)
    else:
        eventos = Evento.objects.filter(tipo_de_evento=evento_id, endDate__year=configuracao.ano, endDate__month__gt=6)
    return eventos.order_by("endDate", "startDate").last()

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_professor(request):
    """Mostra página principal do usuário professor."""

    configuracao = get_object_or_404(Configuracao)
    PRAZO = int(get_object_or_404(Configuracao).prazo_avaliar)  # prazo para preenchimentos de avaliações

    context = {"titulo": "Área dos Professores",}
    if request.user.tipo_de_usuario in [2,4]:  # Professor ou Administrador
        projetos = Projeto.objects.filter(orientador=request.user.professor, ano=configuracao.ano, semestre=configuracao.semestre)

        if projetos:

            # Verifica se todos os projetos do professor orientador têm o plano de orientação
            tipo_documento = TipoDocumento.objects.get(nome="Plano de Orientação")
            feito = True
            planos_de_orientacao = 'b'
            for projeto in projetos:
                feito = feito and Documento.objects.filter(tipo_documento=tipo_documento, projeto=projeto).exists()
            if feito:
                planos_de_orientacao = 'g'
            else:
                evento = get_evento(10, configuracao)  # (10, "Início das aulas", "#FF1010"),
                if evento:
                    planos_de_orientacao = 'b'
                    context["planos_de_orientacao__prazo"] = evento.endDate + datetime.timedelta(days=(PRAZO+5))
                    if datetime.date.today() < evento.endDate:
                        planos_de_orientacao = 'b'
                    elif datetime.date.today() > context["planos_de_orientacao__prazo"]:
                        planos_de_orientacao = 'r'
                    else:
                        planos_de_orientacao = 'y'
            context["planos_de_orientacao"] = planos_de_orientacao

            # Verifica se todos os projetos do professor orientador têm as avaliações dos relatos quinzenais
            relatos_quinzenais = 'b'
            for projeto in projetos:
                for evento, relatos, avaliados, observacoes in projeto.get_relatos():
                    if evento and (not evento.em_prazo()):  # Prazo para estudantes, assim ja deviam ter sido avaliados ou em vias de.
                        if relatos:
                            if avaliados and relatos_quinzenais != 'r' and relatos_quinzenais != 'y':
                                relatos_quinzenais = 'g'
                            else:
                                if evento and evento.endDate and datetime.date.today() > evento.endDate + datetime.timedelta(days=PRAZO):
                                    relatos_quinzenais = 'r'
                                else:
                                    if relatos_quinzenais != 'r':
                                        relatos_quinzenais = 'y'
                        else:
                            if relatos_quinzenais != 'r' and relatos_quinzenais != 'y':
                                relatos_quinzenais = 'g'
            context["relatos_quinzenais"] = relatos_quinzenais

            # Verifica se todos os projetos do professor orientador têm as avaliações das entregas
            avaliar_entregas = 'b'
            composicoes = filtra_composicoes(Composicao.objects.filter(entregavel=True), projeto.ano, projeto.semestre)
            for projeto in projetos:
                entregas = filtra_entregas(composicoes, projeto)
                for item in entregas:
                    if item["evento"] and item["evento"].endDate:
                        dias_passados = datetime.date.today() - item["evento"].endDate
                        if dias_passados.days > 0:
                            if item["composicao"] and item["composicao"].exame:
                                if item["composicao"].exame.grupo:
                                    for documento in item["documentos"]:
                                        if item["avaliacoes"]:
                                            diff_entrega = (documento.data - item["avaliacoes"].first().momento)
                                            if diff_entrega.days > PRAZO:
                                                avaliar_entregas = 'r'  # Nova avaliação urgente!
                                            elif diff_entrega.total_seconds() > 0:
                                                if avaliar_entregas != 'r':
                                                    avaliar_entregas = 'y'  # Nova avaliação pendente!
                                            else:
                                                if avaliar_entregas != 'r' and avaliar_entregas != 'y':
                                                    avaliar_entregas = 'g'  # Avaliação feita!
                                        else:
                                            if dias_passados.days > PRAZO:
                                                avaliar_entregas = 'r'  # Avaliação urgente!
                                            else:
                                                if avaliar_entregas != 'r':
                                                    avaliar_entregas = 'y'  # Avaliação pendente!
                                else:
                                    if item["alocacoes"]:
                                        for _, values in item["alocacoes"].items():
                                            for documento in values["documentos"]:
                                                if values["avaliacoes"]:
                                                    diff_entrega = (documento.data - values["avaliacoes"].first().momento)
                                                    if diff_entrega.days > PRAZO:
                                                        avaliar_entregas = 'r'  # Nova avaliação urgente!
                                                    elif diff_entrega.total_seconds() > 0:
                                                        if avaliar_entregas != 'r':
                                                            avaliar_entregas = 'y'  # Nova avaliação pendente!
                                                    else:
                                                        if avaliar_entregas != 'r' and avaliar_entregas != 'y':
                                                            avaliar_entregas = 'g'  # Avaliação feita!
                                                else:
                                                    if dias_passados.days > PRAZO:
                                                        avaliar_entregas = 'r'  # Avaliação urgente!
                                                    else:
                                                        if avaliar_entregas != 'r':
                                                            avaliar_entregas = 'y'  # Avaliação pendente!
            context["avaliar_entregas"] = avaliar_entregas

            # Verifica se todos os projetos do professor orientador têm os agendamentos E AVALIAÇÕES COMPLETAS das bancas
            bancas_index = 'b'
            banca = Banca.objects.filter(projeto=projeto, tipo_de_banca=1).exists()  # (1, 'Intermediária'),
            evento = get_evento(14, configuracao)  # (14, "Bancas Intermediárias", "#EE82EE"),
            if evento and (datetime.date.today() - evento.startDate).days > -16:
                if banca:
                    bancas_index = 'g'
                else:
                    if evento and (datetime.date.today() - evento.startDate).days > -9:
                        bancas_index = 'r'
                    else:
                        bancas_index = 'y'
            banca = Banca.objects.filter(projeto=projeto, tipo_de_banca=0).exists()  # (0, 'Final')
            evento = get_evento(15, configuracao)  # (15, "Bancas Finais", "#FFFF00"),
            if evento and (datetime.date.today() - evento.startDate).days > -16:
                if banca:
                    bancas_index = 'g'
                else:
                    if evento and (datetime.date.today() - evento.startDate).days > -9:
                        bancas_index = 'r'
                    else:
                        bancas_index = 'y'
            context["bancas_index"] = bancas_index

            # Verifica se todos os projetos do professor orientador têm as avaliações de pares conferidas
            avaliacoes_pares = 'b'
            evento = get_evento(31, configuracao)  # (31, "Avaliação de Pares Intermediária", "#FFC0CB"),
            if evento and (datetime.date.today() - evento.startDate).days > 0:
                feito = True
                for projeto in projetos:
                    for alocacao in Alocacao.objects.filter(projeto=projeto):
                        if Pares.objects.filter(alocacao_de=alocacao, tipo=0).first():  # Intermediaria
                            feito = feito and alocacao.avaliacao_intermediaria
                if feito and avaliacoes_pares != 'r' and avaliacoes_pares != 'y':
                    avaliacoes_pares = 'g'
                else:
                    if evento and (datetime.date.today() - evento.endDate).days > PRAZO:
                        avaliacoes_pares = 'r'
                    elif avaliacoes_pares != 'r':
                        avaliacoes_pares = 'y'
            evento = get_evento(32, configuracao)  #(32, "Avaliação de Pares Final", "#FFC0DB"),
            if evento and (datetime.date.today() - evento.startDate).days > 0:
                feito = True
                for projeto in projetos:
                    for alocacao in Alocacao.objects.filter(projeto=projeto):
                        if Pares.objects.filter(alocacao_de=alocacao, tipo=1).first():  # Final
                            feito = feito and alocacao.avaliacao_final
                if feito and avaliacoes_pares != 'r' and avaliacoes_pares != 'y':
                    avaliacoes_pares = 'g'
                else:
                    if evento and (datetime.date.today() - evento.endDate).days > PRAZO:
                        avaliacoes_pares = 'r'
                    elif avaliacoes_pares != 'r':
                        avaliacoes_pares = 'y'
            context["avaliacoes_pares"] = avaliacoes_pares
        
    
    if "/professores/professores" in request.path:
        return render(request, "professores/professores.html", context=context)
    else:
        return render(request, "professores/index_professor.html", context=context)
    


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def avaliacoes_pares(request, todos=None):
    """Formulários com os projetos e relatos a avaliar do professor orientador."""

    if todos == "todos" and request.user.tipo_de_usuario != 4:  # Administrador
        return HttpResponse("Acesso negado.", status=401)

    context = {"titulo": "Avaliações de Pares"}

    if request.user.tipo_de_usuario == 4:  # Administrador
        context["administracao"] = True

    if request.is_ajax():
        if "edicao" in request.POST:

            projetos = Projeto.objects.filter(ano__gte=2023).order_by("ano", "semestre")  # 2023 é o ano que comecou a avaliacao de pares no sistema do PFE

            if todos != "todos":
                projetos = projetos.filter(orientador=request.user.professor)

            edicao = request.POST["edicao"]
            if edicao != "todas":
                ano, semestre = map(int, edicao.split('.'))
                projetos = projetos.filter(ano=ano, semestre=semestre)
            context["projetos"] = projetos
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Pares)
        context["edicoes"] = edicoes

    return render(request, "professores/avaliacoes_pares.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_alocadas(request):
    """Mostra detalhes sobre o professor."""
    bancas = (Banca.objects.filter(membro1=request.user) |
              Banca.objects.filter(membro2=request.user) |
              Banca.objects.filter(membro3=request.user))
    
    if request.user.professor:
        bancas = bancas | Banca.objects.filter(projeto__orientador=request.user.professor)
        bancas = bancas | Banca.objects.filter(projeto__coorientador__usuario=request.user)

    context = {
        "titulo": "Participação em Bancas",
        "bancas": bancas.order_by("-startDate"),
        }
    return render(request, "professores/bancas_alocadas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def orientacoes_alocadas(request):
    """Mostra detalhes sobre o professor."""
    projetos = Projeto.objects.filter(orientador=request.user.professor).order_by("-ano", "-semestre")
    context = {
        "titulo": "Projetos Orientados",
        "projetos": projetos,
        }
    return render(request, "professores/orientacoes_alocadas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def coorientacoes_alocadas(request):
    """Mostra detalhes sobre o professor."""
    coorientacoes = Coorientador.objects.filter(usuario=request.user)\
        .order_by("-projeto__ano", "-projeto__semestre")
    context = {
        "titulo": "Projetos Coorientados",
        "coorientacoes": coorientacoes,
        }
    return render(request, "professores/coorientacoes_alocadas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mentorias_alocadas(request):
    """Mostra detalhes sobre o professor."""
    mentorias = Encontro.objects.exclude(endDate__lt=datetime.date.today(), projeto__isnull=True)
    mentorias = mentorias.filter(facilitador=request.user).order_by("-projeto__ano", "-projeto__semestre", "startDate")
    context = {
        "titulo": "Mentorias Facilitadas",
        "mentorias": mentorias,
        }
    return render(request, "professores/mentorias_alocadas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_index(request):
    """Menus de bancas e calendario de bancas."""
    # 14, 'Banca intermediária' / 15, 'Bancas finais' / 50, 'Certificação Profissional (antiga Falconi)', / 18, 'Probation'
    dias_bancas = Evento.objects.filter(tipo_de_evento__in=(14, 15, 18, 50))

    context = {
        "titulo": "Agendar Bancas",
        "dias_bancas": dias_bancas,
        "view": request.GET.get("view", None),
        "date": request.GET.get("date", None),
        "usuario": request.user,
    }

    return render(request, "professores/bancas_index.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def ajax_bancas(request):
    """Retorna as bancas do ano."""

    if request.is_ajax():
        
        if "start" in request.POST and "end" in request.POST:
            start = datetime.datetime.strptime(request.POST["start"], "%Y-%m-%d").date() - datetime.timedelta(days=90)
            end = datetime.datetime.strptime(request.POST["end"], "%Y-%m-%d").date() + datetime.timedelta(days=90)
            bancas = {}
            for banca in Banca.objects.filter(startDate__gte=start,
                                              startDate__lte=end):
                bancas[banca.id] = {}
                bancas[banca.id]["start"] = banca.startDate.strftime("%Y-%m-%dT%H:%M:%S")
                bancas[banca.id]["end"] = banca.endDate.strftime("%Y-%m-%dT%H:%M:%S")
                bancas[banca.id]["local"] = banca.location

                if banca.projeto:
                    bancas[banca.id]["organizacao"] = banca.projeto.organizacao.sigla if banca.projeto.organizacao else None
                    bancas[banca.id]["orientador"] = banca.projeto.orientador.user.get_full_name() if banca.projeto.orientador else None
                    bancas[banca.id]["membro1"] = banca.membro1.get_full_name() if banca.membro1 else ""
                    bancas[banca.id]["membro2"] = banca.membro2.get_full_name() if banca.membro2 else ""
                    bancas[banca.id]["membro3"] = banca.membro3.get_full_name() if banca.membro3 else ""

                    if request.user.tipo_de_usuario == 4:  # Administrador
                        bancas[banca.id]["editable"] = True
                    elif banca.projeto.orientador and request.user.professor:
                        bancas[banca.id]["editable"] = banca.projeto.orientador == request.user.professor
                    else:
                        bancas[banca.id]["editable"] = False

                    title = "[" + banca.projeto.organizacao.sigla + "] " + banca.projeto.get_titulo()
                    if banca.location:
                        title += "\nLocal: " + banca.location
                    title += "\nBanca:"
                    if banca.projeto.orientador:
                        title += "\n• " + banca.projeto.orientador.user.get_full_name() + " (O)"
                    for membro in banca.membros():
                        title += "\n• " + membro.get_full_name()
                elif banca.alocacao:
                    bancas[banca.id]["organizacao"] = banca.alocacao.projeto.organizacao.sigla if banca.alocacao.projeto.organizacao else None
                    bancas[banca.id]["orientador"] = banca.alocacao.projeto.orientador.user.get_full_name() if banca.alocacao.projeto.orientador else None
                    bancas[banca.id]["membro1"] = banca.membro1.get_full_name() if banca.membro1 else ""
                    bancas[banca.id]["membro2"] = banca.membro2.get_full_name() if banca.membro2 else ""
                    bancas[banca.id]["membro3"] = banca.membro3.get_full_name() if banca.membro3 else ""

                    if request.user.tipo_de_usuario == 4:  # Administrador
                        bancas[banca.id]["editable"] = True
                    elif banca.alocacao.projeto.orientador and request.user.professor:
                        bancas[banca.id]["editable"] = banca.alocacao.projeto.orientador == request.user.professor
                    else:
                        bancas[banca.id]["editable"] = False

                    title = "Estudante: " + banca.alocacao.aluno.user.get_full_name()
                    title += " - [" + banca.alocacao.projeto.organizacao.sigla + "] " + banca.alocacao.projeto.get_titulo()
                    if banca.location:
                        title += "\nLocal: " + banca.location
                    title += "\nBanca:"
                    if banca.alocacao.projeto.orientador:
                        title += "\n• " + banca.alocacao.projeto.orientador.user.get_full_name() + " (O)"
                    for membro in banca.membros():
                        title += "\n• " + membro.get_full_name()
                else:
                    title = "Projeto ou alocação não identificados",
                bancas[banca.id]["title"] = title
                
                if banca.tipo_de_banca == 0: # Banca Final
                    bancas[banca.id]["color"] = "#74a559"
                    bancas[banca.id]["className"] = "b_final"
                elif banca.tipo_de_banca == 1:  # Banca Intermediária
                    bancas[banca.id]["color"] = "#e6b734"
                    bancas[banca.id]["className"] = "b_intermediaria"
                elif banca.tipo_de_banca == 2: # Banca Falconi
                    bancas[banca.id]["color"] = "#ff38a6"
                    bancas[banca.id]["className"] = "b_falconi"
                elif banca.tipo_de_banca == 3: # Probation
                    bancas[banca.id]["color"] = "#FF8C00"
                    bancas[banca.id]["className"] = "b_probation"
                else:
                    bancas[banca.id]["color"] = "#777777"

                if banca.projeto:
                    description = "[" + banca.projeto.organizacao.sigla + "] " + banca.projeto.get_titulo()
                elif banca.alocacao:
                    description = "Estudante: " + banca.alocacao.aluno.user.get_full_name()
                    description += " - [" + banca.alocacao.projeto.proposta.organizacao.nome + "] " + banca.alocacao.projeto.get_titulo()
                else:
                    description = "Projeto não identificado"

                if banca.location:
                    description += "\n<br>Local: " + banca.location

                description += "\n<br>Banca:"
                if banca.projeto and banca.projeto.orientador:
                    description += "\n<br>&bull; " + banca.projeto.orientador.user.get_full_name() + " (O)"
                for membro in banca.membros():
                    description += "\n<br>&bull; " + membro.get_full_name()

                bancas[banca.id]["description"] = description
                
            return JsonResponse(bancas)
    
    return HttpResponse("Erro.", status=401)    


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def ajax_atualiza_banca(request):
    """Atualiza os dados de uma banca por ajax."""

    if request.is_ajax():
        
        if "id" in request.POST and "start" in request.POST and "end" in request.POST:
            start = datetime.datetime.strptime(request.POST["start"], "%d/%m/%Y, %H:%M")
            end = datetime.datetime.strptime(request.POST["end"], "%d/%m/%Y, %H:%M")
            banca = Banca.objects.get(id = request.POST["id"])
            banca.startDate = start
            banca.endDate = end
            banca.save()

            context = {"atualizado": True,}
            return JsonResponse(context)
    
    return HttpResponse("Erro.", status=401)    



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def ajax_atualiza_dinamica(request):
    """Atualiza os dados de uma dinamica por ajax."""

    if request.is_ajax():
        
        if "id" in request.POST and "start" in request.POST and "end" in request.POST:
            start = datetime.datetime.strptime(request.POST["start"], "%d/%m/%Y, %H:%M")
            end = datetime.datetime.strptime(request.POST["end"], "%d/%m/%Y, %H:%M")
            encontro = Encontro.objects.get(id = request.POST["id"])
            encontro.startDate = start
            encontro.endDate = end
            encontro.save()

            context = {"atualizado": True,}
            return JsonResponse(context)
    
    return HttpResponse("Erro.", status=401)    


def mensagem_edicao_banca(banca, atualizada=False, excluida=False, enviar=False):

    error_message = None

    subject = "Capstone | Banca "
    if banca.tipo_de_banca == 0:
        subject += "Final "
    elif banca.tipo_de_banca == 1:
        subject += "Intermediária "
    elif banca.tipo_de_banca == 2:
        subject += "Falconi "
    elif banca.tipo_de_banca == 3:
        subject += "Probation "
    
    if excluida:
        subject += "Cancelada"
    else:
        subject += "Reagendada" if atualizada else "Agendada"

    if banca.tipo_de_banca == 3:
        projeto = banca.alocacao.projeto
        subject += " - Estudante: " + banca.alocacao.aluno.user.get_full_name() + " [" + projeto.organizacao.nome + "] " + projeto.get_titulo()
    else:
        projeto = banca.projeto
        subject += " - Projeto: [" + projeto.proposta.organizacao.nome + "] " + projeto.get_titulo()

    if excluida:
        mensagem = '<span style="color: red; font-weight: bold;">Banca Capstone Cancelada.</span><br><br>'
    elif atualizada:
        mensagem = '<span style="color: ##FF5733; font-weight: bold;">Banca Capstone Reagendada.</span><br><br>'
    else:
        mensagem = "Banca Capstone Agendada.<br><br>"

    mensagem += "Projeto: [" + projeto.proposta.organizacao.nome + "] " + projeto.get_titulo() + "<br>"

    if banca.tipo_de_banca == 0:
        mensagem += "Tipo: Banca Final<br>"
    elif banca.tipo_de_banca == 1:
        mensagem += "Tipo: Banca Intermediária<br>"
    elif banca.tipo_de_banca == 2:
        mensagem += "Tipo: Banca Falconi<br>"
    elif banca.tipo_de_banca == 3:
        mensagem += "Tipo: Banca Probation<br>"

    if banca.location:
        mensagem += "Local: " + banca.location + "<br>"

    if banca.link:
        mensagem += "Link: " + banca.link + "<br>"

    mensagem += "Data: " + banca.startDate.strftime("%d/%m/%Y das %H:%M") + " às " + banca.endDate.strftime("%H:%M") + "<br><br>"

    BLOQUEAR = True
    configuracao = get_object_or_404(Configuracao)
    if not excluida:
        total_bancas = Banca.objects.all().count()
        nao_intersecta = Banca.objects.filter(Q(endDate__lte=banca.startDate) | Q(startDate__gte=banca.endDate)).count()
        if (total_bancas - nao_intersecta - 1) >= configuracao.limite_salas_bancas:  # -1 para nao contar a propria banca

            if BLOQUEAR:
                return "Mais de duas bancas agendadas para o mesmo horário! Agendamento não realizado."
            
            mensagem += "<span style='color: red; font-weight: bold;'>"
            mensagem += "Mais de duas bancas agendadas para o mesmo horário!<br>"
            mensagem += "Agendamento realizado, contudo poderá não ser possível alocar uma sala para esse horário.<br>"
            mensagem += "</span><br>"

    recipient_list = []

    mensagem += 'Membros da Banca:<br><ul style="margin-top: 2px;">'

    # Orientador
    if projeto.orientador:
        mensagem += "<li>" + projeto.orientador.user.get_full_name() + " [orientador] "
        mensagem += '<a href="mailto:' + projeto.orientador.user.email + '">&lt;' + projeto.orientador.user.email + "&gt;</a></li>"
        recipient_list.append(projeto.orientador.user.email)

    # coorientadores
    for coorientador in projeto.coorientador_set.all():
        mensagem += "<li>" + coorientador.usuario.get_full_name() + " [coorientador] "
        mensagem += '<a href="mailto:' + coorientador.usuario.email + '">&lt;' + coorientador.usuario.email + "&gt;</a></li>"
        recipient_list.append(coorientador.usuario.email)

    # membros
    for membro in banca.membros():
        mensagem += "<li>" + membro.get_full_name() + " [membro da banca] "
        mensagem += '<a href="mailto:' + membro.email + '">&lt;' + membro.email + "&gt;</a></li>"
        recipient_list.append(membro.email)
    mensagem += "</ul>"

    mensagem += 'Grupo de Estudantes:<br><ul style="margin-top: 2px;">'

    # estudantes
    for alocacao in projeto.alocacao_set.all():
        mensagem += "<li>" + alocacao.aluno.user.get_full_name()
        mensagem += " [" + str(alocacao.aluno.curso2) + "] "
        mensagem += '<a href="mailto:' + alocacao.aluno.user.email + '">&lt;' + alocacao.aluno.user.email + "&gt;</a></li>"
        recipient_list.append(alocacao.aluno.user.email)
    mensagem += "</ul>"

    # Adiciona coordenacao e operacaos
    configuracao = get_object_or_404(Configuracao)
    if configuracao.coordenacao:
        recipient_list.append(str(configuracao.coordenacao.user.email))
    if configuracao.operacao:
        recipient_list.append(str(configuracao.operacao.email))

    if enviar:
        check = email(subject, recipient_list, mensagem)
        if check != 1:
            error_message = "Problema no envio de e-mail, subject=" + subject + ", message_email=" + mensagem + ", recipient_list=" + str(recipient_list)
            logger.error(error_message)
    
    return error_message
    
@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_criar(request, data=None):
    """Cria uma banca de avaliação para o projeto."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax() and request.method == "POST":

        atualizado = True
        mensagem, banca = editar_banca(None, request)
        if mensagem is None:
            mensagem_edicao_banca(banca, enviar=("enviar_mensagem" in request.POST)) # Atualizada
        else:
            atualizado = False

        context = {
            "atualizado": atualizado,
            "mensagem": mensagem,
        }
        return JsonResponse(context)

    ano = configuracao.ano
    semestre = configuracao.semestre
    projetos = Projeto.objects.filter(ano=ano, semestre=semestre).exclude(orientador=None)
    alocacoes = Alocacao.objects.filter(projeto__ano=ano, projeto__semestre=semestre)

    professores, _ = professores_membros_bancas()
    falconis, _ = falconi_membros_banca()

    # Coletando bancas agendadas a partir de hoje
    hoje = datetime.date.today()
    bancas_agendadas = Banca.objects.filter(startDate__gt=hoje).order_by("startDate")
    projetos_agendados = list(bancas_agendadas.values_list("projeto", flat=True))

    if configuracao.semestre == 1:
        eventos = Evento.objects.filter(startDate__year=configuracao.ano, startDate__month__lt=7)
    else:
        eventos = Evento.objects.filter(startDate__year=configuracao.ano, startDate__month__gt=7)

    # 14, 'Banca intermediária' / 15, 'Bancas finais' / 50, 'Certificação Falconi' / 18, 'Probation'
    bancas_intermediarias = eventos.filter(tipo_de_evento=14)
    bancas_finais = eventos.filter(tipo_de_evento=15)
    bancas_probation = eventos.filter(tipo_de_evento=18)
    bancas_falconi = eventos.filter(tipo_de_evento=50)

    context = {
        "projetos": projetos,
        "alocacoes": alocacoes,
        "professores": professores,
        "Banca": Banca,
        # "TIPO_DE_BANCA": Banca.TIPO_DE_BANCA,
        # Para ficar na ordem que desejo
        "TIPO_DE_BANCA": ((1, 'Intermediária'), (0, 'Final'), (2, 'Certificação Falconi'), (3, 'Probation')),
        "falconis": falconis,
        "projetos_agendados": projetos_agendados,
        "bancas_intermediarias": bancas_intermediarias,
        "bancas_finais": bancas_finais,
        "bancas_probation": bancas_probation,
        "bancas_falconi": bancas_falconi,
        "url": request.get_full_path(),
    }

    if data:
        context["data"] = data[:10]  # soh a data, tirando a hora se for o caso
        datar = datetime.datetime.strptime(context["data"], "%Y-%m-%d").date()
        if bancas_finais and bancas_finais.first().startDate and bancas_finais.last().endDate:
            if datar >= bancas_finais.first().startDate and datar <= bancas_finais.last().endDate:
                context["tipob"] = 0
        if bancas_intermediarias and bancas_intermediarias.first().startDate and bancas_intermediarias.last().endDate:
            if datar >= bancas_intermediarias.first().startDate and datar <= bancas_intermediarias.last().endDate:
                context["tipob"] = 1
        if bancas_falconi and bancas_falconi.first().startDate and bancas_falconi.last().endDate:
            if datar >= bancas_falconi.first().startDate and datar <= bancas_falconi.last().endDate:
                context["tipob"] = 2
        if bancas_probation and bancas_probation.first().startDate and bancas_probation.last().endDate:
            if datar >= bancas_probation.first().startDate and datar <= bancas_probation.last().endDate:
                context["tipob"] = 3
        
    return render(request, "professores/bancas_view.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mensagem_email(request, tipo=None, primarykey=None):
    """Envia mensagens."""

    if primarykey is None:
        return HttpResponseNotFound("<h1>Erro!</h1>")

    # Envia mensagem diretamente
    if request.is_ajax() and request.method == "POST":

        mensagem = ""
        if "assunto" in request.POST and "para" in request.POST and "mensagem" in request.POST:
            assunto = request.POST["assunto"]
            para = request.POST["para"]
            mensagem = request.POST["mensagem"]
        else:
            return HttpResponse("Envio não realizado.", status=401)

        recipient_list = para.split(';')
        recipient_list.append("Luciano Pereira Soares <lpsoares@insper.edu.br>")

        check = email(assunto, recipient_list, mensagem)
        if check != 1:
            error_message = "Problema no envio de e-mail, subject=" + subject + ", message=" + message + ", recipient_list=" + str(recipient_list)
            logger.error(error_message)

        context = {
                "atualizado": True,
                "mensagem": mensagem,
            }
        return JsonResponse(context)
    
    if tipo == "banca":
    
        banca = get_object_or_404(Banca, pk=primarykey)
        projeto = banca.get_projeto()

        para = ""
        if projeto and projeto.orientador:
            para += projeto.orientador.user.get_full_name() + " <" + projeto.orientador.user.email + ">; "
        for coorientador in projeto.coorientador_set.all():
            para += coorientador.usuario.get_full_name() + " <" + coorientador.usuario.email + ">; "
        for membro in banca.membros():
            para += membro.get_full_name() + " <" + membro.email + ">; "
        
        if banca.alocacao:
            subject = "Capstone | Banca: " + banca.alocacao.aluno.user.get_full_name() + " [" + banca.alocacao.projeto.organizacao.nome + "] " +  banca.alocacao.projeto.get_titulo()
        else:
            subject = "Capstone | Banca: [" + projeto.organizacao.nome + "] " +  projeto.get_titulo()
        
        context_carta = {
            "request": request,
            "banca": banca,
        }
        message = render_message("Mensagem Banca", context_carta)

    elif tipo == "certificado":
    
        certificado = get_object_or_404(Certificado, pk=primarykey)
        configuracao = get_object_or_404(Configuracao)

        para = ""
        if certificado.usuario:
            para += certificado.usuario.get_full_name() + " <" + certificado.usuario.email + ">"

        subject = "Capstone | Certificado: "
        if certificado.tipo_de_certificado == 101: subject += "Orientação de Projeto"
        elif certificado.tipo_de_certificado == 102: subject += "Coorientação de Projeto"
        elif certificado.tipo_de_certificado == 103: subject += "Membro de Banca Intermediária"
        elif certificado.tipo_de_certificado == 104: subject += "Membro de Banca Final"
        elif certificado.tipo_de_certificado == 105: subject += "Membro de Banca Falconi"
        elif certificado.tipo_de_certificado == 106: subject += "Mentoria de Projeto"
        elif certificado.tipo_de_certificado == 107: subject += "Mentoria de Projeto"
        elif certificado.tipo_de_certificado == 108: subject += "Membro de Banca de Probation"
        
        context_carta = {
            "request": request,
            "configuracao": configuracao,
            "certificado": certificado,
        }
        message = render_message("Mensagem Certificado", context_carta)

    para = para.strip()
    if para[-1] == ";":
        para = para[:-1]  # tirando o ultimo ";"

    context = {
        "assunto": subject,
        "para": para,
        "mensagem": message,
        "url": request.get_full_path(),
    }
    return render(request, "professores/mensagem_email.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_editar(request, primarykey=None):
    """Edita uma banca de avaliação para o projeto."""
    configuracao = get_object_or_404(Configuracao)

    if primarykey is None:
        return HttpResponseNotFound("<h1>Erro!</h1>")

    banca = get_object_or_404(Banca, pk=primarykey)

    if request.is_ajax() and request.method == "POST":

        atualizado = True
        mensagem = ""
        if "atualizar" in request.POST:
            mensagem, _ = editar_banca(banca, request)
            if mensagem is None:
                mensagem_edicao_banca(banca, True, enviar=("enviar_mensagem" in request.POST)) # Atualizada
            else:
                atualizado = False
        elif "excluir" in request.POST:
            mensagem_edicao_banca(banca, True, True, enviar=("enviar_mensagem" in request.POST)) # Excluída
            if "projeto" in request.POST:
                banca.delete()
        else:
            return HttpResponse("Atualização não realizada.", status=401)

        context = {
                "atualizado": atualizado,
                "mensagem": mensagem,
            }
        return JsonResponse(context)
    
    ano = configuracao.ano
    semestre = configuracao.semestre
    projetos = Projeto.objects.filter(ano=ano, semestre=semestre).exclude(orientador=None)
    alocacoes = Alocacao.objects.filter(projeto__ano=ano, projeto__semestre=semestre)

    professores, _ = professores_membros_bancas()
    falconis, _ = falconi_membros_banca()

    configuracao = get_object_or_404(Configuracao)
    if configuracao.semestre == 1:
        eventos = Evento.objects.filter(startDate__year=configuracao.ano, startDate__month__lt=7)
    else:
        eventos = Evento.objects.filter(startDate__year=configuracao.ano, startDate__month__gt=7)

    # 14, "Banca intermediária" / 15, "Bancas finais" / 50, "Certificação Falconi"
    bancas_intermediarias = eventos.filter(tipo_de_evento=14).order_by("startDate")
    bancas_finais = eventos.filter(tipo_de_evento=15).order_by("startDate")
    bancas_probation = eventos.filter(tipo_de_evento=18).order_by("startDate")
    bancas_falconi = eventos.filter(tipo_de_evento=50).order_by("startDate")

    context = {
        "projetos": projetos,  # Creio que não seja necessário
        "alocacoes": alocacoes,   # Creio que não seja necessário
        "professores": professores,
        "banca": banca,
        "Banca": Banca,
        "TIPO_DE_BANCA": ((1, "Intermediária"), (0, "Final"), (2, "Certificação Falconi"), (3, "Probation")), # Para ficar na ordem que desejo
        "falconis": falconis,
        "bancas_intermediarias": bancas_intermediarias,
        "bancas_finais": bancas_finais,
        "bancas_probation": bancas_probation,
        "bancas_falconi": bancas_falconi,
        "url": request.get_full_path(),
    }
    return render(request, "professores/bancas_view.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_lista(request, periodo_projeto):
    """Lista as bancas agendadas, conforme periodo ou projeto pedido."""
    context = {
        "titulo": "Listagem das Bancas",
        "periodo": periodo_projeto
        }

    if periodo_projeto == "proximas":
        # Coletando bancas agendadas a partir de hoje
        hoje = datetime.date.today()
        bancas = Banca.objects.filter(startDate__gt=hoje).order_by("startDate")

        # checando se projetos atuais tem banca marcada
        configuracao = get_object_or_404(Configuracao)
        projetos = Projeto.objects.filter(ano=configuracao.ano,
                                          semestre=configuracao.semestre)
        for banca in bancas:
            if banca.projeto:
                projetos = projetos.exclude(id=banca.projeto.id)
        context["sem_banca"] = projetos

    elif periodo_projeto == "todas":
        bancas = Banca.objects.all().order_by("startDate")

    elif '.' in periodo_projeto:
        periodo = periodo_projeto.split('.')
        try:
            ano = int(periodo[0])
            semestre = int(periodo[1])
        except ValueError:
            return HttpResponseNotFound("<h1>Erro em!</h1>")

        bancas_p = Banca.objects.filter(projeto__ano=ano)\
            .filter(projeto__semestre=semestre)

        bancas_a = Banca.objects.filter(alocacao__projeto__ano=ano)\
            .filter(alocacao__projeto__semestre=semestre)

        bancas = (bancas_p | bancas_a).order_by("startDate")

    else:
        projeto = get_object_or_404(Projeto, id=periodo_projeto)
        context["projeto"] = projeto
        bancas = Banca.objects.filter(projeto=projeto).order_by("startDate")

    context["bancas"] = bancas

    edicoes, _, _ = get_edicoes(Projeto)
    context["edicoes"] = edicoes

    # (14, "Bancas Intermediárias", "#EE82EE"),
    # (15, "Bancas Finais", "#FFFF00"),
    # (18, "Probation", "#B0C4DE"),
    # (50, "Apresentação para Certificação Falconi", "#FF8C00"),
    context["dias_bancas"] = Evento.objects.filter(tipo_de_evento__in=(14, 15, 18, 50))

    context["informacoes"] = [
            (".local", "local"),
            (".link", "video-conferência"),
            (".grupo", "grupo"),
            (".orientacao", "orientação"),
            (".curso", "curso"),
            (".banca", "avaliadores"),
            (".avaliacao", "link avaliação"),
            (".agendamento", "agendamento"),
            (".email", "e-mail"),
            (".editar", "editar"),
            (".sem_agendamento", "sem agendamento"),
        ]
    
    return render(request, "professores/bancas_lista.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_tabela(request):
    """Lista todas as bancas agendadas, conforme periodo pedido."""
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                bancas = Banca.objects.all()
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    bancas = Banca.objects.filter(projeto__ano=ano)
                else:
                    bancas = Banca.objects.filter(projeto__ano=ano).filter(projeto__semestre=semestre)

            membros = dict()
            
            for banca in bancas:
                if banca.projeto.orientador:
                    if banca.tipo_de_banca != 2:  # Nao eh Falconi
                        membros.setdefault(banca.projeto.orientador.user, []).append(banca)
                for membro in banca.membros():
                    membros.setdefault(membro, []).append(banca)

        context = {"membros": membros,}

    else:
        edicoes, _, _ = get_edicoes(Projeto, anual=True)
        context = {"edicoes": edicoes,}

    return render(request, "professores/bancas_tabela.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mentorias_tabela(request):
    """Lista todas as mentorias agendadas, conforme periodo pedido."""
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                mentorias = Encontro.objects.all()
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    mentorias = Encontro.objects.filter(projeto__ano=ano)
                else:
                    mentorias = Encontro.objects.filter(projeto__ano=ano).filter(projeto__semestre=semestre)

            mentores = dict()
            for mentoria in mentorias.filter(projeto__isnull=False):
                mentores.setdefault(mentoria.facilitador, []).append(mentoria)

        context = {"mentores": mentores,}

    else:
        edicoes, _, _ = get_edicoes(Projeto, anual=True)
        context = {"edicoes": edicoes,}

    return render(request, "professores/mentorias_tabela.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def aulas_tabela(request):
    """Lista todas as aulas agendadas, conforme periodo pedido."""
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            if edicao == "todas":
                aulas = Evento.objects.filter(tipo_de_evento=12)   #.order_by("endDate", "startDate").last()
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    aulas = Evento.objects.filter(tipo_de_evento=12, endDate__year=ano)
                elif semestre == '1':
                    aulas = Evento.objects.filter(tipo_de_evento=12, endDate__year=ano, endDate__month__lt=7)
                else:  # semestre == '2':
                    aulas = Evento.objects.filter(tipo_de_evento=12, endDate__year=ano, endDate__month__gt=6)

        context = {"aulas": aulas,}

    else:
        edicoes, _, _ = get_edicoes(Projeto, anual=True)
        context = {"edicoes": edicoes,}

    return render(request, "professores/aulas_tabela.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_tabela_completa(request):
    """Lista todas as bancas agendadas, conforme periodo pedido."""
    configuracao = get_object_or_404(Configuracao)

    membros_pfe = []
    periodo = []

    ano = 2018
    semestre = 2
    while True:
        membros = dict()
        bancas = Banca.objects.all().filter(projeto__ano=ano)\
            .filter(projeto__semestre=semestre)
        for banca in bancas:
            if banca.projeto.orientador:
                membros.setdefault(banca.projeto.orientador.user, [])\
                    .append(banca)
            for membro in banca.membros():
                membros.setdefault(membro, []).append(banca)

        membros_pfe.append(membros)
        periodo.append(str(ano)+"."+str(semestre))

        if ((ano == configuracao.ano) and (semestre == configuracao.semestre)):
            break

        if semestre == 2:
            semestre = 1
            ano += 1
        else:
            semestre = 2

    # inverti lista deixando os mais novos primeiro
    anos = zip(membros_pfe[::-1], periodo[::-1])

    informacoes = [
        ("#MembrosTable tr > *:nth-child(2)", "e-mail"),
        ("#MembrosTable tr > *:nth-child(3)", "Quantidade"),
        ("#MembrosTable tr > *:nth-child(4)", "Projetos"),
    ]

    context = {
        "anos": anos,
        "informacoes": informacoes,
    }

    return render(request, "professores/bancas_tabela_completa.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def banca_ver(request, primarykey):
    """Retorna banca pedida."""
    banca = get_object_or_404(Banca, id=primarykey)
    if banca.tipo_de_banca == 1:  # (1, "intermediaria"),
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Intermediária") | TipoDocumento.objects.filter(nome="Relatório Intermediário de Grupo")
    elif banca.tipo_de_banca == 0:  # (0, "final"),
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    elif banca.tipo_de_banca == 2:  # (2, "falconi"),
        # Repetindo banca final para falconi
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    elif banca.tipo_de_banca == 3:  # (3, "probation"),
        # Repetindo banca final para probation
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    else:
        tipo_documento = TipoDocumento.objects.none()

    documentos = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.projeto).order_by("tipo_documento", "-data")

    context = {
        "titulo": "Banca " + banca.get_tipo_de_banca_display() + " [" + banca.projeto.organizacao.sigla + "] " + banca.projeto.get_titulo(),
        "banca": banca,
        "documentos": documentos,
    }

    return render(request, "professores/banca_ver.html", context)


# Mensagem preparada para o avaliador
def mensagem_avaliador(banca, avaliador, julgamento, julgamento_observacoes, objetivos_possiveis, realizada):
    
    message = "{0},<br><br>\n".format(avaliador.get_full_name())
    message += "Obrigado por sua avaliação de banca no Capstone (antigo PFE)<br><br>\n"
    message += "Estamos também informando o orientador do projeto sobre sua avaliação<br><br>\n"

    if realizada:
        message += "<h3 style='color:red;text-align:center;'>"
        message += "Essa é uma atualização de uma avaliação já enviada anteriormente!"
        message += "</h3><br><br>"

    if banca.tipo_de_banca == 3:
        projeto = banca.alocacao.projeto
    else:
        projeto = banca.projeto

    message += "<b>Título do Projeto:</b> {0}<br>\n".format(projeto.get_titulo())
    message += "<b>Organização:</b> {0}<br>\n".format(projeto.organizacao)
    message += "<b>Orientador:</b> {0}<br>\n".format(projeto.orientador)
    message += "<b>Avaliador:</b> {0}<br>\n".format(avaliador.get_full_name())
    message += "<b>Data da Banca:</b> {0}<br>\n".format(banca.startDate.strftime("%d/%m/%Y %H:%M"))

    message += "<b>Tipo de Banca:</b> "
    tipos = dict(Banca.TIPO_DE_BANCA)
    if banca.tipo_de_banca in tipos:
        message += tipos[banca.tipo_de_banca]
    else:
        message += "Tipo de banca não definido"

    if banca.alocacao:
        message += "<br><b>Estudante em Probation:</b> {0}<br>\n".format(banca.alocacao.aluno.user.get_full_name())

    message += "<br>\n<br>\n"
    message += "<b>Conceitos:</b><br>\n"
    message += "<table style='border: 1px solid black; "
    message += "border-collapse:collapse; padding: 0.3em;'>"

    for i in range(objetivos_possiveis):
        if julgamento[i]:
            message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                format(julgamento[i].objetivo.titulo)
            message += "<td style='border: 1px solid black; text-align:center'>"
            if julgamento[i].na:
                message += "&nbsp;N/A&nbsp;</td>\n"
            else:
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[i].nota))
                
    message += "</table>"

    message += "<br>\n<br>\n"

    if julgamento_observacoes and julgamento_observacoes.observacoes_estudantes:
        message += "<b>Observações Estudantes (enviada para todo o grupo):</b>\n"
        message += "<p style='border:1px; border-style:solid; padding: 0.3em; margin: 0;'>"
        message += html.escape(julgamento_observacoes.observacoes_estudantes).replace('\n', '<br>\n')
        message += "</p>"
        message += "<br>\n<br>\n"

    if julgamento_observacoes and julgamento_observacoes.observacoes_orientador:
        message += "<b>Observações Orientador (somente enviada para orientador):</b>\n"
        message += "<p style='border:1px; border-style:solid; padding: 0.3em; margin: 0;'>"
        message += html.escape(julgamento_observacoes.observacoes_orientador).replace('\n', '<br>\n')
        message += "</p>"
        message += "<br>\n<br>\n"

    # Criar link para reeditar
    message += "<a href='" + settings.SERVER
    message += "/professores/banca_avaliar/" + str(banca.slug)

    message += "?avaliador=" + str(avaliador.id)
    for count, julg in enumerate(julgamento):
        if julg and not julg.na:
            message += "&objetivo" + str(count) + "=" + str(julg.objetivo.id)
            message += "&conceito" + str(count) + "=" + converte_letra(julg.nota, mais="X")
    if julgamento_observacoes and julgamento_observacoes.observacoes_orientador:
        message += "&observacoes_orientador=" + quote(julgamento_observacoes.observacoes_orientador)
    if julgamento_observacoes and julgamento_observacoes.observacoes_estudantes:
        message += "&observacoes_estudantes=" + quote(julgamento_observacoes.observacoes_estudantes)    
    message += "'>"
    message += "Caso deseje reenviar sua avaliação, clique aqui."
    message += "</a><br>\n"
    message += "<br>\n"

    # Relistar os Objetivos de Aprendizagem
    message += "<br><b>Objetivos de Aprendizagem</b>"

    destaque = " background-color: #E0E0F4;'>"

    for julg in julgamento:

        if julg:

            message += "<br><b>{0}</b>: {1}".format(julg.objetivo.titulo, julg.objetivo.objetivo)
            message += "<table "
            message += "style='border:1px solid black; border-collapse:collapse; width:100%;'>"
            message += "<tr>"

            if (not julg.na) and converte_letra(julg.nota) == "I":
                message += "<td style='border: 2px solid black; width:18%;"
                message += destaque
            else:
                message += "<td style='border: 1px solid black; width:18%;'>"
            message += "Insatisfatório (I)</th>"

            if (not julg.na) and converte_letra(julg.nota) == "D":
                message += "<td style='border: 2px solid black; width:18%;"
                message += destaque
            else:
                message += "<td style='border: 1px solid black; width:18%;'>"
            message += "Em Desenvolvimento (D)</th>"

            if (not julg.na) and (converte_letra(julg.nota) == "C" or converte_letra(julg.nota) == "C+"):
                message += "<td style='border: 2px solid black; width:18%;"
                message += destaque
            else:
                message += "<td style='border: 1px solid black; width:18%;'>"
            message += "Essencial (C/C+)</th>"

            if (not julg.na) and (converte_letra(julg.nota) == "B" or converte_letra(julg.nota) == "B+"):
                message += "<td style='border: 2px solid black; width:18%;"
                message += destaque
            else:
                message += "<td style='border: 1px solid black; width:18%;'>"
            message += "Proficiente (B/B+)</th>"

            if (not julg.na) and (converte_letra(julg.nota) == "A" or converte_letra(julg.nota) == "A+"):
                message += "<td style='border: 2px solid black; width:18%;"
                message += destaque
            else:
                message += "<td style='border: 1px solid black; width:18%;'>"
            message += "Avançado (A/A+)</th>"

            message += "</tr>"


            message += "<tr " 
            if julg.na:
                message += " style='background-color: #151515;'"
            message += ">"

            if (not julg.na) and converte_letra(julg.nota) == "I":
                message += "<td style='border: 2px solid black;"
                message += destaque
            else:
                message += "<td style='border: 1px solid black;'>"
            if banca.tipo_de_banca == 1:
                message += "{0}".format(julg.objetivo.rubrica_intermediaria_I)
            else:
                message += "{0}".format(julg.objetivo.rubrica_final_I)

            message += "</td>"

            if (not julg.na) and (converte_letra(julg.nota) == "D-" or converte_letra(julg.nota) == "D" or converte_letra(julg.nota) == "D+"):
                message += "<td style='border: 2px solid black;"
                message += destaque
            else:
                message += "<td style='border: 1px solid black;'>"
            if banca.tipo_de_banca == 1:
                message += "{0}".format(julg.objetivo.rubrica_intermediaria_D)
            else:
                message += "{0}".format(julg.objetivo.rubrica_final_D)
            message += "</td>"

            if (not julg.na) and (converte_letra(julg.nota) == "C" or converte_letra(julg.nota) == "C+"):
                message += "<td style='border: 2px solid black;"
                message += destaque
            else:
                message += "<td style='border: 1px solid black;'>"
            if banca.tipo_de_banca == 1:
                message += "{0}".format(julg.objetivo.rubrica_intermediaria_C)
            else:
                message += "{0}".format(julg.objetivo.rubrica_final_C)
            message += "</td>"

            if (not julg.na) and (converte_letra(julg.nota) == "B" or converte_letra(julg.nota) == "B+"):
                message += "<td style='border: 2px solid black;"
                message += destaque
            else:
                message += "<td style='border: 1px solid black;'>"
            if banca.tipo_de_banca == 1:
                message += "{0}".format(julg.objetivo.rubrica_intermediaria_B)
            else:
                message += "{0}".format(julg.objetivo.rubrica_final_B)
            message += "</td>"

            if (not julg.na) and (converte_letra(julg.nota) == "A" or converte_letra(julg.nota) == "A+"):
                message += "<td style='border: 2px solid black;"
                message += destaque
            else:
                message += "<td style='border: 1px solid black;'>"
            if banca.tipo_de_banca == 1:
                message += "{0}".format(julg.objetivo.rubrica_intermediaria_A)
            else:
                message += "{0}".format(julg.objetivo.rubrica_final_A)
            message += "</td>"

            message += "</tr>"
            message += "</table>"

    return message


def calcula_notas_bancas(avaliadores):
    obj_avaliados = {}
    
    message2 = "<table>"
    for avaliador, objs in avaliadores.items():
        
        message2 += "<tr><td>"
        message2 += "<strong>Avaliador"
        if avaliador.genero == "F":
            message2 += "a"
        message2 += ": </strong>"
        message2 += avaliador.get_full_name() + "<br>"

        if "momento" in objs:
            message2 += "<strong>Avaliado em: </strong>"
            message2 += objs["momento"].strftime('%d/%m/%Y às %H:%M') + "<br>"

        message2 += "<strong>Conceitos:</strong><br>"

        message2 += "<ul style='margin-top: 0px;'>"

        for objetivo, conceito in objs.items():
            if objetivo != "momento" and objetivo != "observacoes_estudantes" and objetivo != "observacoes_orientador":
                message2 += "<li>"
                message2 += objetivo.titulo
                message2 += " : "
                if conceito.nota is not None:
                    message2 += converte_conceitos(conceito.nota)                
                    message2 += "</li>"
                    if objetivo.titulo in obj_avaliados:
                        obj_avaliados[objetivo.titulo]["nota"] += conceito.nota
                        obj_avaliados[objetivo.titulo]["qtd"] += 1
                    else:
                        obj_avaliados[objetivo.titulo] = {}
                        obj_avaliados[objetivo.titulo]["nota"] = conceito.nota
                        obj_avaliados[objetivo.titulo]["qtd"] = 1
                else:
                    message2 += "N/A</li>"

        if "observacoes_estudantes" in objs and objs["observacoes_estudantes"]:
            message2 += "<li>Observações Estudantes: " + objs["observacoes_estudantes"] + "</li>"
        if "observacoes_orientador" in objs and objs["observacoes_orientador"]:
            message2 += "<li>Observações Orientador: " + objs["observacoes_orientador"] + "</li>"
        
        message2 += "</ul>"
        message2 += "</td></tr>"


    message2 += "</td></tr>"
    message2 += "</table>"

    return message2, obj_avaliados

def calcula_media_notas_bancas(obj_avaliados):
    message = ""
    message += "<div style='color: red; border-width:3px; border-style:solid; border-color:#ff0000; display: inline-block; padding: 10px;'>"
    message += "<b> Média das avaliações: "
    message += "<ul>"
    medias = 0
    for txt, obj in obj_avaliados.items():
        if obj["qtd"] > 0.0:
            message += "<li>"
            message += txt
            message += ": "
            media = obj["nota"]/obj["qtd"]
            medias += arredonda_conceitos(media)
            message += converte_conceitos(media)
            message += "</li>"
        else:
            message += "<li>N/A</li>"

    message += "</ul>"
    
    message += "&#10149; Nota Final Calculada = "
    if len(obj_avaliados):
        message += '<span>'
        message += "<b style='font-size: 1.16em;'>"
        message += "%.2f" % (medias/len(obj_avaliados))
        message += "</b><br>"
        message += '</span>'
    else:
        message += '<span>N/A</span>'

    message += "</b></div><br><br>"

    return message


# Mensagem preparada para o orientador/coordenador
def mensagem_orientador(banca):
    objetivos = ObjetivosDeAprendizagem.objects.all()

    # Trocando tipo de banca para tipo de avaliação
    if banca.tipo_de_banca == 0: #Banca Final
        exame = Exame.objects.get(titulo="Banca Final")
    elif banca.tipo_de_banca == 1: #Banca Itermediária
        exame = Exame.objects.get(titulo="Banca Intermediária")
    elif banca.tipo_de_banca == 2: #Banca Falconi
        exame = Exame.objects.get(titulo="Falconi")
    elif banca.tipo_de_banca == 3: #Banca Probation
        exame = Exame.objects.get(titulo="Probation")

    if banca.tipo_de_banca == 3:
        projeto = banca.alocacao.projeto
    else:
        projeto = banca.projeto

    # Buscando Avaliadores e Avaliações
    avaliadores = {}
    for objetivo in objetivos:
        avaliacoes = Avaliacao2.objects.filter(projeto=projeto,
                                                objetivo=objetivo,
                                                exame=exame)\
                .order_by("avaliador", "-momento")
        if banca.alocacao:
            avaliacoes = avaliacoes.filter(alocacao=banca.alocacao)

        for avaliacao in avaliacoes:
            if avaliacao.avaliador not in avaliadores:
                avaliadores[avaliacao.avaliador] = {}
            if objetivo not in avaliadores[avaliacao.avaliador]:
                avaliadores[avaliacao.avaliador][objetivo] = avaliacao
                avaliadores[avaliacao.avaliador]["momento"] = avaliacao.momento

    observacoes = Observacao.objects.filter(projeto=projeto, exame=exame).\
        order_by("avaliador", "-momento")
    if banca.alocacao:
        observacoes = observacoes.filter(alocacao=banca.alocacao)

    for observacao in observacoes:
        if observacao.avaliador not in avaliadores:
            avaliadores[observacao.avaliador] = {}  # Não devia acontecer isso
        if "observacoes_orientador" not in avaliadores[observacao.avaliador]:
            avaliadores[observacao.avaliador]["observacoes_orientador"] = observacao.observacoes_orientador
        if "observacoes_estudantes" not in avaliadores[observacao.avaliador]:
            avaliadores[observacao.avaliador]["observacoes_estudantes"] = observacao.observacoes_estudantes

    message3, obj_avaliados = calcula_notas_bancas(avaliadores)
    message2 = calcula_media_notas_bancas(obj_avaliados)

    context_carta = {
        "banca": banca,
        "objetivos": objetivos,
        "projeto": projeto,
    }
    message = render_message("Informe de Avaliação de Banca", context_carta)
    
    return message+message2+message3


@transaction.atomic
def banca_avaliar(request, slug, documento_id=None):
    """Cria uma tela para preencher avaliações de bancas."""
    configuracao = get_object_or_404(Configuracao)
    coordenacao = configuracao.coordenacao
    
    prazo_preencher_banca = configuracao.prazo_preencher_banca

    mensagem = ""

    try:
        banca = Banca.objects.get(slug=slug)

        adm = PFEUser.objects.filter(pk=request.user.pk, tipo_de_usuario=4).exists()  # se adm

        vencida = banca.endDate.date() + datetime.timedelta(days=prazo_preencher_banca) < datetime.date.today()

        if vencida:  # prazo vencido
            mensagem += "<div style='border: 2px solid red; width: fit-content; padding: 6px;'>Prazo de submissão da Avaliação de Banca vencido.<br>"
            mensagem += "Data do encerramento da banca: " + banca.endDate.strftime("%d/%m/%Y - %H:%M:%S") + "<br>"
            mensagem += "Número de dias de prazo para preenchimento: " + str(prazo_preencher_banca) + " dias.</div><br>"
            mensagem += "Entre em contato com a coordenação do PFE para enviar sua avaliação:<br>"
            mensagem += coordenacao.user.get_full_name()
            mensagem += " <a href='mailto:" + coordenacao.user.email + "'>"
            mensagem += " &lt;" + coordenacao.user.email + "&gt;</a>.<br>"

        if vencida and (not adm):  # se administrador passa direto
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)

        if banca.projeto is None and banca.alocacao is None:
            return HttpResponseNotFound("<h1>Banca não registrada corretamente!</h1>")

    except Banca.DoesNotExist:
        return HttpResponseNotFound('<h1>Banca não encontrada!</h1>')

    if banca.tipo_de_banca == 3:  # (3, 'probation')
        projeto = banca.alocacao.projeto
    else:
        projeto = banca.projeto

    # Usado para pegar o relatório de avaliação de banca para usuários não cadastrados
    if documento_id:
        documento = Documento.objects.get(id=documento_id, projeto=projeto)
        path = str(documento.documento).split('/')[-1]
        local_path = os.path.join(settings.MEDIA_ROOT, "{0}".format(documento.documento))
        diferenca = (datetime.date.today() - banca.endDate.date()).days
        if diferenca > configuracao.prazo_preencher_banca:
            return HttpResponseNotFound("<h1>Link expirado!<br> Documentos só podem ser visualizados até " + str(configuracao.prazo_preencher_banca) + " dias após a data da banca!</h1>")
        return le_arquivo(request, local_path, path, bypass_confidencial=True)

    ####################################################################################
    # ISSO ESTÁ OBSOLETO
    # Subistituir por:     objetivos = composicao.pesos.all()
    objetivos = get_objetivos_atuais(ObjetivosDeAprendizagem.objects.all())
    # Banca(Intermediária, Final, Probation) ou Falconi
    if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1:
        objetivos = objetivos.filter(avaliacao_banca=True)
    elif banca.tipo_de_banca == 2:  # Falconi
        objetivos = objetivos.filter(avaliacao_falconi=True)
    elif banca.tipo_de_banca == 3:  # Probation
        objetivos = objetivos.filter(avaliacao_aluno=True)
    else:
        return HttpResponseNotFound("<h1>Tipo de Banca não indentificado</h1>")
    ####################################################################################
    
    if request.method == "POST":
        if "avaliador" in request.POST:

            avaliador = get_object_or_404(PFEUser,
                                          pk=int(request.POST["avaliador"]))

            if banca.tipo_de_banca == 1:  # (1, 'intermediaria'),
                exame = Exame.objects.get(titulo="Banca Intermediária")
            elif banca.tipo_de_banca == 0:  # (0, 'final'),
                exame = Exame.objects.get(titulo="Banca Final")
            elif banca.tipo_de_banca == 2:  # (2, 'falconi'),
                exame = Exame.objects.get(titulo="Falconi")
            elif banca.tipo_de_banca == 3:  # (3, 'probation'),
                exame = Exame.objects.get(titulo="Probation")

            # Identifica que uma avaliação/observação já foi realizada anteriormente
            avaliacoes_anteriores = Avaliacao2.objects.filter(projeto=projeto, avaliador=avaliador, exame=exame)
            observacoes_anteriores = Observacao.objects.filter(projeto=projeto, avaliador=avaliador, exame=exame)
            if banca.alocacao:
                avaliacoes_anteriores = avaliacoes_anteriores.filter(alocacao=banca.alocacao)
                observacoes_anteriores = observacoes_anteriores.filter(alocacao=banca.alocacao)
            
            realizada = avaliacoes_anteriores.exists()

            # Mover avaliação anterior para base de dados de Avaliações Velhas
            move_avaliacoes(avaliacoes_anteriores, observacoes_anteriores)

            objetivos_possiveis = len(objetivos)
            julgamento = [None]*objetivos_possiveis
            
            avaliacoes = dict(filter(lambda elem: elem[0][:9] == "objetivo.", request.POST.items()))

            for i, aval in enumerate(avaliacoes):

                obj_nota = request.POST[aval]
                conceito = obj_nota.split('.')[1]
                julgamento[i] = Avaliacao2.create(projeto=projeto)
                if banca.alocacao:
                    julgamento[i].alocacao = banca.alocacao
                julgamento[i].avaliador = avaliador

                pk_objetivo = int(obj_nota.split('.')[0])
                julgamento[i].objetivo = get_object_or_404(ObjetivosDeAprendizagem,
                                                            pk=pk_objetivo)

                julgamento[i].exame = exame

                if conceito == "NA":
                    julgamento[i].na = True
                else:
                    julgamento[i].nota = converte_conceito(conceito)

                    if exame.titulo == "Banca Intermediária":    
                        julgamento[i].peso = julgamento[i].objetivo.peso_banca_intermediaria
                    elif exame.titulo == "Banca Final":
                        julgamento[i].peso = julgamento[i].objetivo.peso_banca_final
                    elif exame.titulo == "Falconi":
                        julgamento[i].peso = julgamento[i].objetivo.peso_banca_falconi
                    elif exame.titulo == "Probation":
                        #julgamento[i].peso = julgamento[i].objetivo.peso_banca_probation
                        julgamento[i].peso = 0.0
                    else:
                        julgamento[i].peso = 0.0 

                    julgamento[i].na = False
                julgamento[i].save()

            julgamento_observacoes = None
            if ("observacoes_orientador" in request.POST and request.POST["observacoes_orientador"] != "") or \
               ("observacoes_estudantes" in request.POST and request.POST["observacoes_estudantes"] != ""):
                julgamento_observacoes = Observacao.create(projeto=projeto)
                if banca.alocacao:
                    julgamento_observacoes.alocacao = banca.alocacao
                julgamento_observacoes.avaliador = avaliador
                if "observacoes_orientador" in request.POST:
                    julgamento_observacoes.observacoes_orientador = request.POST["observacoes_orientador"]
                if "observacoes_estudantes" in request.POST:
                    julgamento_observacoes.observacoes_estudantes = request.POST["observacoes_estudantes"]
                julgamento_observacoes.exame = exame
                julgamento_observacoes.save()


            subject = "Capstone | Avaliação de Banca "
            if banca.tipo_de_banca == 0:
                subject += "Banca Final : "
            elif banca.tipo_de_banca == 1:
                subject += "Banca Intermediária : " 
            elif banca.tipo_de_banca == 2:
                subject += "Banca Falconi : "
            elif banca.tipo_de_banca == 3:
                subject += "Probation : " + banca.alocacao.aluno.user.get_full_name()
            subject += " [" + projeto.organizacao.sigla + "] " + projeto.get_titulo()
            
            # Envio de mensagem para Avaliador
            message = mensagem_avaliador(banca, avaliador, julgamento, julgamento_observacoes, objetivos_possiveis, realizada)
            recipient_list = [avaliador.email, ]
            check = email(subject, recipient_list, message)
            if check != 1:
                error_message = "Problema no envio de e-mail, subject=" + subject + ", message=" + message + ", recipient_list=" + str(recipient_list)
                logger.error(error_message)

            # Envio de mensagem para Orientador / Coordenação
            message = mensagem_orientador(banca)
            # Intermediária e Final
            if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1:
                recipient_list = [projeto.orientador.user.email, ]
            else: # banca.tipo_de_banca == 2 or banca.tipo_de_banca == 3:  # Falconi ou Probation
                recipient_list = [coordenacao.user.email, ]
            check = email(subject, recipient_list, message)
            if check != 1:
                error_message = "Problema no envio de e-mail, subject=" + subject + ", message=" + message + ", recipient_list=" + str(recipient_list)
                logger.error(error_message)
            
            resposta = "Avaliação submetida e enviada para:<br>"
            for recipient in recipient_list:
                resposta += "&bull; {0}<br>".format(recipient)
            if realizada:
                resposta += "<br><br><h2>Essa é uma atualização de uma avaliação já enviada anteriormente!</h2><br><br>"
            resposta += "<br><a href='javascript:history.back(1)'>Voltar</a>"
            context = {
                "area_principal": True,
                "mensagem": resposta,
            }
            return render(request, "generic.html", context=context)

        return HttpResponse("Avaliação não submetida.")
    else:

        orientacoes = ""
        orientacoes_en = ""

        # Intermediária e Final
        if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1:
            pessoas, membros = professores_membros_bancas(banca)
            orientacoes += "Os orientadores são responsáveis por conduzir a banca. Os membros do grupo terão <b>40 minutos para a apresentação</b>. Os membros da banca terão depois <b>50 minutos para arguição</b> (que serão divididos pelos membros convidados), podendo tirar qualquer dúvida a respeito do projeto e fazerem seus comentários. Caso haja muitas interferências da banca durante a apresentação do grupo, poderá se estender o tempo de apresentação. A dinâmica de apresentação é livre, contudo, <b>todos os membros do grupo devem estar prontos para responder qualquer tipo de pergunta</b> sobre o projeto, assim um membro da banca pode fazer uma pergunta direcionada para um estudante específico do grupo se desejar. Caso o grupo demore mais que os 40 minutos a banca poderá definir uma punição em um objetivo de aprendizado, idealmente no objetivo de Comunicação."
            orientacoes += "<br><br>"
            orientacoes += "Como ordem recomendada para a arguição da banca, se deve convidar: professores convidados, professores coorientadores, orientador(a) do projeto e por fim demais pessoas assistindo à apresentação. A banca poderá perguntar tanto sobre a apresentação, como o relatório entregue, permitindo uma clara ponderação nas rubricas dos objetivos de aprendizado."
            orientacoes += "<br><br>"
            orientacoes += "As bancas do Projeto Final de Engenharia servem como mais um evidência de aprendizado, assim, além da percepção dos membros da banca em relação ao nível alcançado nos objetivos de aprendizado pelos membros do grupo, serve também como registro da evolução do projeto. Dessa forma, ao final, a banca terá mais <b>15 minutos para ponderar</b>, nesse momento se pede para dispensar os estudantes e demais convidados externos. Recomendamos 5 minutos para os membros da banca relerem os objetivos de aprendizagem e rubricas, fazerem qualquer anotação e depois 10 minutos para uma discussão final. Cada membro da banca poderá colocar seu veredito sobre grupo, usando as rubricas a seguir."
            orientacoes += "<br><br>"
            orientacoes += "No Projeto Final de Engenharia, a maioria dos projetos está sob sigilo, através de contratos realizados (quando pedido ou necessário) entre a Organização Parceira e o Insper, se tem os professores automaticamente responsáveis por garantir o sigilo das informações. Assim <b>pessoas externas só podem participar das bancas com prévia autorização</b>, isso inclui outros estudantes que não sejam do grupo, familiares ou amigos."
            orientacoes += "<br>"

            orientacoes_en += "The advisors are responsible for leading the presentation. The group members will have <b>40 minutes for the presentation</b>. The evaluation committee members will then have <b>50 minutes for the discussion</b> (which will be divided by the invited members), being able to ask any questions about the project and make their comments. If there is a lot of interference from the examination members during the group's presentation, the presentation time may be extended. <b>all group members should be ready to answer any kind of question</b> about the project, so an evaluation committee member can ask a question directed at a specific student in the group if desired. If a group takes longer than 40 minutes, the evaluation committee will be able to define a punishment in a learning objective, ideally in the Communication objective."
            orientacoes_en += "<br><br>"
            orientacoes_en += "As recommended order for the evaluation committee members's argument, the following should be invited: guest professors, co-advisor professors, project supervisor and finally other people watching the presentation. The evaluation committee may ask about the presentation, as well as the report delivered, enabling a clear weighting for the learning objectives rubrics."
            orientacoes_en += "<br><br>"
            orientacoes_en += "Presentations of the Final Engineering Project serve as another evidence of learning, thus, in addition to the perception of the members of the evaluation committee in relation to the level reached in the learning objectives by the members of the group, it also serves as a record of the evolution of the project. In this way, at the end, the evaluation committee will have more <b>15 minutes to consider</b>, at which point they are asked to dismiss students and other external guests. We recommend 5 minutes for panel members to reread the learning objectives and rubrics, make any notes, and then 10 minutes for a final discussion. Each evaluation committee member will be able to define a verdict for the group, using the rubrics below."
            orientacoes_en += "<br><br>"
            orientacoes_en += "In the Final Engineering Project, most projects are kept confidential, through contracts made (when requested or necessary) between the Partner Organization and Insper, the professors are automatically responsible for guaranteeing the confidentiality of the information. <b>external people can only participate in the presentaions with prior authorization</b>, this includes other students who are not part of the group, family or friends."
            orientacoes_en += "<br>"
            
        
        # Falconi
        elif banca.tipo_de_banca == 2:
            pessoas, membros = falconi_membros_banca(banca)
            orientacoes += "Os membros do grupo terão <b>10 minutos para a apresentação</b>. Os consultores da Falconi terão depois outros <b>15 minutos para arguição e observações</b>, podendo tirar qualquer dúvida a respeito do projeto e fazerem seus comentários. Caso haja interferências durante a apresentação do grupo, poderá se estender o tempo de apresentação. A dinâmica de apresentação é livre, contudo, <b>todos os membros do grupo devem estar prontos para responder qualquer tipo de pergunta</b> sobre o projeto. Um consultor da Falconi pode fazer uma pergunta direcionada para um estudante específico do grupo se desejar."
            orientacoes += "<br><br>"
            orientacoes += "As apresentações para a comissão de consultores da Falconi serão usadas para avaliar os melhores projetos. Cada consultor da Falconi poderá colocar seu veredito sobre grupo, usando as rubricas a seguir. Ao final a coordenação do PFE irá fazer a média das avaliações e os projetos que atingirem os níveis de excelência pré-estabelecidos irão receber o certificado de destaque."
            orientacoes += "<br><br>"
            orientacoes += "No Projeto Final de Engenharia, a maioria dos projetos está sob sigilo, através de contratos realizados (quando pedido ou necessário) entre a Organização Parceira e o Insper. A Falconi assinou um documento de responsabilidade em manter o sigilo das informações divulgadas nas apresentações. Assim <b>pessoas externas só podem participar das bancas com prévia autorização</b>, isso inclui outros estudantes que não sejam do grupo, familiares ou amigos."
            orientacoes += "<br>"

            orientacoes_en += "Group members will have <b>15 minutes for the presentation</b>. Falconi consultants will then have another <b>15 minutes for discussion and observations</b>, being able to clarify any doubts about the project and make their comments. If there is interference during the group presentation, the presentation time may be extended. The presentation dynamics is free, however, <b>all group members must be ready to answer any type of question< /b> about the project. A Falconi consultant can ask a question directed at a specific student in the group if desired."
            orientacoes_en += "<br><br>"
            orientacoes_en += "The presentations to Falconi's commission of consultants will be used to evaluate the best projects. Each Falconi consultant will be able to put his verdict on the group, using the following rubrics. At the end, the PFE coordination will average the evaluations and the projects that reach the pre-established levels of excellence will receive the outstanding certificate."
            orientacoes_en += "<br><br>"
            orientacoes_en += "In the Final Engineering Project, most projects are kept confidential, through contracts made (when requested or necessary) between the Partner Organization and Insper. Falconi signed a document of responsibility to maintain the confidentiality of the information disclosed in the presentations. So <b>external people can only participate in the stands with prior authorization</b>, this includes other students who are not part of the group, family or friends."
            orientacoes_en += "<br>"


        # Probation
        elif banca.tipo_de_banca == 3:
            pessoas, membros = professores_membros_bancas(banca)
            orientacoes += "O estudante em Probation terá <b>20 minutos para a apresentação</b>. Os membros da banca terão depois <b>40 minutos para arguição</b> (que serão divididos pelos membros convidados), podendo tirar qualquer dúvida a respeito da atuação do estudante e fazerem seus comentários."
            orientacoes += "<br><br>"
            orientacoes += "A banca poderá perguntar tanto sobre a apresentação, como os relatórios entregues (individual ou de grupo), permitindo uma clara ponderação nas rubricas dos objetivos de aprendizado."
            orientacoes += "<br><br>"
            orientacoes += "Ao final, a banca terá mais <b>20 minutos para ponderar</b>, nesse momento se pede para dispensar o estudante. Cada membro da banca poderá colocar seu veredito sobre o estudante, usando as rubricas a seguir."
            orientacoes += "<br><br>"

            orientacoes_en += ""

        # Identificando quem seria o avaliador
        if "avaliador" in request.GET:
            try:
                avaliador_id = int(request.GET.get("avaliador", '0'))  # Carregando dados REST
            except ValueError:
                return HttpResponseNotFound("<h1>Usuário não encontrado!</h1>")
        else:
            if request.user and request.user.is_authenticated:
                avaliador_id = request.user.pk
            else:
                avaliador_id = None
        
        conceitos = [None]*len(objetivos)
        for i in range(len(objetivos)):
            try:
                tmp_objetivo = int(request.GET.get("objetivo"+str(i), '0'))
            except ValueError:
                return HttpResponseNotFound("<h1>Erro em objetivo!</h1>")
            tmp_conceito = request.GET.get("conceito"+str(i), '')
            conceitos[i] = (tmp_objetivo, tmp_conceito)

        observacoes_orientador = unquote(request.GET.get("observacoes_orientador", ''))
        observacoes_estudantes = unquote(request.GET.get("observacoes_estudantes", ''))
        
        tipo_documento = None
        if banca.tipo_de_banca == 1:  # (1, 'intermediaria'),
            tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Intermediária") | TipoDocumento.objects.filter(nome="Relatório Intermediário de Grupo")
        elif banca.tipo_de_banca == 0:  # (0, 'final'),
            tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
        elif banca.tipo_de_banca == 2:  # (2, 'falconi'),
            tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
        elif banca.tipo_de_banca == 3:  # (3, 'probation'),
            tipo_documento = TipoDocumento.objects.filter(nome="Relatório para Probation") | TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")

        if banca.tipo_de_banca == 3:  # (3, 'probation')
            sub_titulo = banca.alocacao.aluno.user.get_full_name() + " [" + projeto.organizacao.sigla + "] " + projeto.get_titulo()
        else:
            sub_titulo = " [" + projeto.organizacao.sigla + "] " + projeto.get_titulo()

        documentos = None
        if tipo_documento:
            documentos = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=projeto).order_by("tipo_documento", "-data")

        context = {
            "titulo": "Formulário Banca " + banca.get_tipo_de_banca_display() + sub_titulo,
            "projeto": projeto,
            "estudante": banca.alocacao.aluno if banca.tipo_de_banca == 3 else None,
            "individual": True if banca.tipo_de_banca == 3 else False,
            "pessoas": pessoas,
            "membros": membros,
            "objetivos": objetivos,
            "banca": banca,
            "orientacoes": orientacoes,
            "orientacoes_en": orientacoes_en,
            "avaliador": avaliador_id,
            "conceitos": conceitos,
            "documentos": documentos,
            "observacoes_orientador": observacoes_orientador,
            "observacoes_estudantes": observacoes_estudantes,
            "today": datetime.datetime.now(),
            "mensagem": mensagem,
            "periodo_para_rubricas": 1 if banca.tipo_de_banca==1 else 2,  # Dois indices parecidos, mas não iguais
        }
        return render(request, "professores/banca_avaliar.html", context=context)


@transaction.atomic
def banca(request, slug):
    """Somente ve a banca, sem edição."""
    banca = get_object_or_404(Banca, slug=slug)
    if banca.tipo_de_banca == 1:  # (1, "intermediaria"),
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Intermediária") | TipoDocumento.objects.filter(nome="Relatório Intermediário de Grupo")
    elif banca.tipo_de_banca == 0:  # (0, "final"),
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    elif banca.tipo_de_banca == 2:  # (2, "falconi"),
        # Reaproveita o tipo de documento da banca final
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    elif banca.tipo_de_banca == 3:  # (3, "probation"),
        # Reaproveita o tipo de documento da banca final
        tipo_documento = TipoDocumento.objects.filter(nome="Relatório para Probation") | TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    else:
        tipo_documento = None
    
    if tipo_documento:
        documentos = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.projeto).order_by("tipo_documento", "-data")
    else:
        documentos = None

    context = {
        "banca": banca,
        "documentos": documentos,
        "bloqueado": True,
    }

    return render(request, "professores/banca_ver.html", context)

     
@login_required
@permission_required("users.altera_professor", raise_exception=True)
@transaction.atomic
def entrega_avaliar(request, composicao_id, projeto_id, estudante_id=None):
    """Cria uma tela para preencher avaliações de entregas."""
    
    projeto = Projeto.objects.get(pk=projeto_id)
    if request.user != projeto.orientador.user and request.user.tipo_de_usuario != 4:
        return HttpResponseNotFound("<h1>Você não é o orientador desse projeto!</h1>")

    composicao = Composicao.objects.get(pk=composicao_id)

    estudante = None
    if estudante_id:
        estudante = PFEUser.objects.get(pk=estudante_id)
        if estudante.tipo_de_usuario != 1:
            return HttpResponseNotFound("<h1>Pessoa avaliada não é estudante!</h1>")
        alocacao = Alocacao.objects.get(projeto=projeto, aluno=estudante.aluno)

    objetivos = composicao.pesos.all()

    if request.user == projeto.orientador.user:
        editor = True
    else:
        editor = False

    if request.method == "POST":
        
        if objetivos:
            objetivos_possiveis = len(objetivos)
            julgamento = [None]*objetivos_possiveis
            
            avaliacoes = dict(filter(lambda elem: elem[0][:9] == "objetivo.", request.POST.items()))

            nova_avaliacao = True
            for i, aval in enumerate(avaliacoes):

                obj_nota = request.POST[aval]
                conceito = obj_nota.split('.')[1]
                
                pk_objetivo = int(obj_nota.split('.')[0])
                objetivo = get_object_or_404(ObjetivosDeAprendizagem, pk=pk_objetivo)

                if composicao.exame.grupo:
                    avaliacao, nova_avaliacao = Avaliacao2.objects.get_or_create(projeto=projeto, 
                                                                            exame=composicao.exame, 
                                                                            objetivo=objetivo,
                                                                            avaliador=projeto.orientador.user
                                                                            )
                else:
                    if not estudante or not alocacao:
                        return HttpResponseNotFound('<h1>Estudante não encontrado!</h1>')
                    avaliacao, nova_avaliacao = Avaliacao2.objects.get_or_create(projeto=projeto, 
                                                                            exame=composicao.exame, 
                                                                            objetivo=objetivo,
                                                                            avaliador=projeto.orientador.user,
                                                                            alocacao=alocacao
                                                                            )

                julgamento[i] = avaliacao

                if conceito == "NA":
                    julgamento[i].na = True
                else:
                    julgamento[i].nota = converte_conceito(conceito)
                    julgamento[i].peso = Peso.objects.get(composicao=composicao, objetivo=objetivo).peso
                    julgamento[i].na = False
                
                julgamento[i].momento = datetime.datetime.now()

                julgamento[i].save()

        else:
            avaliacao, nova_avaliacao = Avaliacao2.objects.get_or_create(projeto=projeto, 
                                                                    exame=composicao.exame, 
                                                                    objetivo=None,
                                                                    avaliador=projeto.orientador.user
                                                                    )
            
            if "decisao" in request.POST:
                if request.POST["decisao"] == "1":
                    avaliacao.nota = 10
                else:
                    avaliacao.nota = 1  # Zero é um problema pois pode ser confundido com não avaliado
                avaliacao.peso = 0

            avaliacao.momento = datetime.datetime.now()
            avaliacao.save()


        julgamento_observacoes = None
        if ("observacoes_orientador" in request.POST and request.POST["observacoes_orientador"] != "") or \
           ("observacoes_estudantes" in request.POST and request.POST["observacoes_estudantes"] != ""):
            
            if composicao.exame.grupo:
                observacao, _created2 = Observacao.objects.get_or_create(projeto=projeto,
                                                                        exame=composicao.exame,
                                                                        avaliador=projeto.orientador.user
                                                                        )
            else:
                if not estudante or not alocacao:
                    return HttpResponseNotFound('<h1>Estudante não encontrado!</h1>')
                observacao, _created2 = Observacao.objects.get_or_create(projeto=projeto,
                                                                        exame=composicao.exame,
                                                                        avaliador=projeto.orientador.user,
                                                                        alocacao=alocacao
                                                                        )

            julgamento_observacoes = observacao
            julgamento_observacoes.observacoes_orientador = request.POST["observacoes_orientador"]
            julgamento_observacoes.observacoes_estudantes = request.POST["observacoes_estudantes"]
            julgamento_observacoes.momento = datetime.datetime.now()
            julgamento_observacoes.save()


        resposta = "Avaliação concluída com sucesso.<br>"
        if not nova_avaliacao:
            resposta += "<br><br><h2>Essa é uma atualização de uma avaliação já enviada anteriormente!</h2><br><br>"
        resposta += "<br><a href='javascript:history.back(1)'>Voltar</a>"
        context = {
            "area_principal": True,
            "avaliar_entregas": True,
            "mensagem": resposta,
        }
        return render(request, "generic.html", context=context)

    else:  # Não é POST

        if estudante and (not composicao.exame.grupo):
            documentos = Documento.objects.filter(tipo_documento=composicao.tipo_documento, projeto=projeto, usuario=estudante)
        else:
            documentos = Documento.objects.filter(tipo_documento=composicao.tipo_documento, projeto=projeto)

        if projeto.semestre == 1:
            evento = Evento.objects.filter(tipo_de_evento=composicao.evento, endDate__year=projeto.ano, endDate__month__lt=7).last()
        else:          
            evento = Evento.objects.filter(tipo_de_evento=composicao.evento, endDate__year=projeto.ano, endDate__month__gt=6).last()

        if composicao.exame.grupo:
            avaliacoes = Avaliacao2.objects.filter(projeto=projeto, 
                                                exame=composicao.exame, 
                                                avaliador=projeto.orientador.user
                                                )
        else:
            if not estudante or not alocacao:
                return HttpResponseNotFound('<h1>Estudante não encontrado!</h1>')
            avaliacoes = Avaliacao2.objects.filter(projeto=projeto, 
                                                exame=composicao.exame, 
                                                avaliador=projeto.orientador.user,
                                                alocacao=alocacao
                                                )

        conceitos = []
        avaliacao = None
        for i in range(len(avaliacoes)):
            if avaliacoes[i].objetivo:
                tmp_objetivo = avaliacoes[i].objetivo.pk
                tmp_conceito = converte_letra(avaliacoes[i].nota, mais="X")
                conceitos.append( (tmp_objetivo, tmp_conceito) )
            else:
                avaliacao = avaliacoes[i].nota

        if composicao.exame.grupo:
            observacao = Observacao.objects.filter(projeto=projeto,
                                                    exame=composicao.exame,
                                                    avaliador=projeto.orientador.user
                                                ).last()
        else:
            if not estudante or not alocacao:
                return HttpResponseNotFound('<h1>Estudante não encontrado!</h1>')
            observacao = Observacao.objects.filter(projeto=projeto,
                                                    exame=composicao.exame,
                                                    avaliador=projeto.orientador.user,
                                                    alocacao=alocacao
                                                ).last()

        context = {
            "titulo": "Formulário de Avaliação de Entrega",
            "projeto": projeto,
            "composicao": composicao,
            "estudante": estudante,
            "documentos": documentos,
            "evento": evento,
            "periodo_para_rubricas": composicao.exame.periodo_para_rubricas,
            "objetivos": objetivos,
            "today": datetime.datetime.now(),
            "conceitos": conceitos,
            "observacao": observacao,
            "editor": editor,
            "avaliacao": avaliacao,
        }

        return render(request, "professores/entrega_avaliar.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def informe_bancas(request, tipo):
    """Avisa todos os orientadores dos resultados das Bancas Intermediárias."""

    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    #(0, 'Final'),
    #(1, 'Intermediária'),
    
    bancas = Banca.objects.filter(projeto__ano=ano)\
            .filter(projeto__semestre=semestre)\
            .filter(tipo_de_banca=tipo)


    if request.method == "POST":

        for banca in bancas:

            # Envio de mensagem para Orientador / Coordenação
            message = mensagem_orientador(banca)
            subject = "Capstone | Resultado da Avaliação de Banca: {0}".format(banca.projeto)

            recipient_list = [banca.projeto.orientador.user.email, ]
            
            check = email(subject, recipient_list, message)
            if check != 1:
                error_message = "Problema no envio de e-mail, subject=" + subject + ", message=" + message + ", recipient_list=" + str(recipient_list)
                logger.error(error_message)
                message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"
                context = {"mensagem": message,}
                return render(request, "generic.html", context=context)

        resposta = "Informe enviado para:<br>"

        for banca in bancas:
            resposta += "&bull; {0} - banca do dia: {1}<br>".format(banca.projeto.orientador, banca.startDate)

        resposta += "<br><a href='javascript:history.back(1)'>Voltar</a>"

        context = {
            "area_principal": True,
            "mensagem": resposta,
        }

        return render(request, 'generic.html', context=context)

    tipo = "Finais" if tipo==0 else "Intermediárias"
    context = {
        "titulo": "Informe de Bancas " + tipo,
        "bancas": bancas,
        "tipo": tipo,
    }
    return render(request, 'professores/informes_bancas.html', context=context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def conceitos_obtidos(request, primarykey):  # acertar isso para pk
    """Visualiza os conceitos obtidos pelos alunos no projeto."""
    projeto = get_object_or_404(Projeto, pk=primarykey)

    objetivos = ObjetivosDeAprendizagem.objects.all()

    avaliadores_inter = {}
    avaliadores_final = {}
    avaliadores_falconi = {}
    avaliadores_probation = {}

    for objetivo in objetivos:

        # Bancas Intermediárias
        exame = Exame.objects.get(titulo="Banca Intermediária")
        bancas_inter = Avaliacao2.objects.filter(projeto=projeto,
                                                 objetivo=objetivo,
                                                 exame=exame)\
            .order_by("avaliador", "-momento")

        for banca in bancas_inter:
            if banca.avaliador not in avaliadores_inter:
                avaliadores_inter[banca.avaliador] = {}
            if objetivo not in avaliadores_inter[banca.avaliador]:
                avaliadores_inter[banca.avaliador][objetivo] = banca
                avaliadores_inter[banca.avaliador]["momento"] = banca.momento
            # Senão é só uma avaliação de objetivo mais antiga

        # Bancas Finais
        exame = Exame.objects.get(titulo="Banca Final")
        bancas_final = Avaliacao2.objects.filter(projeto=projeto,
                                                 objetivo=objetivo,
                                                 exame=exame)\
            .order_by("avaliador", "-momento")

        for banca in bancas_final:
            if banca.avaliador not in avaliadores_final:
                avaliadores_final[banca.avaliador] = {}
            if objetivo not in avaliadores_final[banca.avaliador]:
                avaliadores_final[banca.avaliador][objetivo] = banca
                avaliadores_final[banca.avaliador]["momento"] = banca.momento
            # Senão é só uma avaliação de objetivo mais antiga

        # Bancas Falconi
        exame = Exame.objects.get(titulo="Falconi")
        bancas_falconi = Avaliacao2.objects.filter(projeto=projeto,
                                                   objetivo=objetivo,
                                                   exame=exame)\
            .order_by("avaliador", "-momento")

        for banca in bancas_falconi:
            if banca.avaliador not in avaliadores_falconi:
                avaliadores_falconi[banca.avaliador] = {}
            if objetivo not in avaliadores_falconi[banca.avaliador]:
                avaliadores_falconi[banca.avaliador][objetivo] = banca
                avaliadores_falconi[banca.avaliador]["momento"] = banca.momento
            # Senão é só uma avaliação de objetivo mais antiga

        # Bancas Probation
        exame = Exame.objects.get(titulo="Probation")
        bancas_probation = Avaliacao2.objects.filter(projeto=projeto,
                                                     objetivo=objetivo,
                                                     exame=exame)\
            .order_by("avaliador", "-momento")
        
        for banca in bancas_probation:
            if banca.avaliador not in avaliadores_probation:
                avaliadores_probation[banca.avaliador] = {}
            if objetivo not in avaliadores_probation[banca.avaliador]:
                avaliadores_probation[banca.avaliador][objetivo] = banca
                avaliadores_probation[banca.avaliador]["momento"] = banca.momento
            # Senão é só uma avaliação de objetivo mais antiga


    # Bancas Intermediárias
    exame = Exame.objects.get(titulo="Banca Intermediária")
    observacoes = Observacao.objects.filter(projeto=projeto, exame=exame).\
        order_by("avaliador", "-momento")
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores_inter:
            avaliadores_inter[observacao.avaliador] = {}  # Não devia acontecer isso
        if "observacoes_estudantes" not in avaliadores_inter[observacao.avaliador]:
            avaliadores_inter[observacao.avaliador]["observacoes_estudantes"] = observacao.observacoes_estudantes
        if "observacoes_orientador" not in avaliadores_inter[observacao.avaliador]:
            avaliadores_inter[observacao.avaliador]["observacoes_orientador"] = observacao.observacoes_orientador
        # Senão é só uma avaliação de objetivo mais antiga

    # Bancas Finais
    exame = Exame.objects.get(titulo="Banca Final")
    observacoes = Observacao.objects.filter(projeto=projeto, exame=exame).\
        order_by("avaliador", "-momento")
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores_final:
            avaliadores_final[observacao.avaliador] = {}  # Não devia acontecer isso
        if "observacoes_estudantes" not in avaliadores_final[observacao.avaliador]:
            avaliadores_final[observacao.avaliador]["observacoes_estudantes"] = observacao.observacoes_estudantes
        if "observacoes_orientador" not in avaliadores_final[observacao.avaliador]:
            avaliadores_final[observacao.avaliador]["observacoes_orientador"] = observacao.observacoes_orientador
        # Senão é só uma avaliação de objetivo mais antiga

    # Bancas Falconi
    exame = Exame.objects.get(titulo="Falconi")
    observacoes = Observacao.objects.filter(projeto=projeto, exame=exame).\
        order_by("avaliador", "-momento")
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores_falconi:
            avaliadores_falconi[observacao.avaliador] = {}  # Não devia acontecer isso
        if "observacoes_estudantes" not in avaliadores_falconi[observacao.avaliador]:
            avaliadores_falconi[observacao.avaliador]["observacoes_estudantes"] = observacao.observacoes_estudantes
        if "observacoes_orientador" not in avaliadores_falconi[observacao.avaliador]:
            avaliadores_falconi[observacao.avaliador]["observacoes_orientador"] = observacao.observacoes_orientador
        # Senão é só uma avaliação de objetivo mais antiga

    # Bancas Probation
    exame = Exame.objects.get(titulo="Probation")
    observacoes = Observacao.objects.filter(projeto=projeto, exame=exame).\
        order_by("avaliador", "-momento")
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores_probation:
            avaliadores_probation[observacao.avaliador] = {}  # Não devia acontecer isso
        if "observacoes_estudantes" not in avaliadores_probation[observacao.avaliador]:
            avaliadores_probation[observacao.avaliador]["observacoes_estudantes"] = observacao.observacoes_estudantes
        if "observacoes_orientador" not in avaliadores_probation[observacao.avaliador]:
            avaliadores_probation[observacao.avaliador]["observacoes_orientador"] = observacao.observacoes_orientador
        # Senão é só uma avaliação de objetivo mais antiga


    context = {
        "titulo": "Resultado Bancas",
        "objetivos": objetivos,
        "projeto": projeto,
        "avaliadores_inter": avaliadores_inter,
        "avaliadores_final": avaliadores_final,
        "avaliadores_falconi": avaliadores_falconi,
        "avaliadores_probation": avaliadores_probation,
    }

    return render(request, "professores/conceitos_obtidos.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_index(request):
    """Menus de encontros."""
    encontros = Encontro.objects.all().order_by("startDate")
    context = {
        "titulo": "Mentorias",
        "encontros": encontros,
        }
    return render(request, "professores/dinamicas_index.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_criar(request, data=None):
    """Cria um encontro."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax() and request.method == "POST":
        
        if ("inicio" in request.POST) and ("fim" in request.POST):

            try:
                startDate = dateutil.parser.parse(request.POST["inicio"])
                endDate = dateutil.parser.parse(request.POST["fim"])
                diferenca = endDate - startDate
            except (ValueError, OverflowError):
                return HttpResponse("Erro com data da Dinâmica!")

            vezes = int(request.POST["vezes"])
            local = request.POST.get("local", None)
            projeto_id = request.POST.get("projeto", None)
            if projeto_id and projeto_id != "0":
                try:
                    projeto = Projeto.objects.get(id=projeto_id)
                except Projeto.DoesNotExist:
                    return HttpResponse("Projeto não encontrado.", status=401)
            else:
                projeto = None
            facilitador_id = request.POST.get("facilitador", None)
            if facilitador_id and facilitador_id != "0":
                try:
                    facilitador = PFEUser.objects.get(id=facilitador_id)
                except PFEUser.DoesNotExist:
                    return HttpResponse("Facilitador não encontrado.", status=401)
            else:
                facilitador = None
                    
            for vez in range(vezes):

                encontro = Encontro.create(startDate+(vez*diferenca), endDate+(vez*diferenca))

                if local:
                    encontro.location = local

                if projeto:
                    encontro.projeto = projeto
                    
                if facilitador:
                    encontro.facilitador = facilitador

                encontro.save()

            if vezes > 1:
                mensagem = "Dinâmicas criadas."
            else:
                mensagem = "Dinâmica criada."
            
            context = {
                "atualizado": True,
                "mensagem": mensagem,
            }
            return JsonResponse(context)

        return HttpResponse("Dinâmica não registrada, erro!", status=401)

    projetos = Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre)

    # Buscando pessoas para lista de Facilitadores
    professores_tmp = PFEUser.objects.filter(tipo_de_usuario=2)  # (2, 'professor')
    administradores = PFEUser.objects.filter(tipo_de_usuario=4)  # (4, 'administrador')
    professores = (professores_tmp | administradores).order_by(Lower("first_name"), Lower("last_name"))

    parceiros = PFEUser.objects.filter(tipo_de_usuario=3)
    organizacao = get_object_or_404(Organizacao, sigla="Falconi")
    falconis = parceiros.filter(parceiro__organizacao=organizacao).order_by(Lower("first_name"), Lower("last_name"))

    # outros_parceiros = parceiros.exclude(parceiro__organizacao=organizacao)
    # estudantes = PFEUser.objects.filter(tipo_de_usuario=1)  # (1, 'estudantes')
    # pessoas = (outros_parceiros | estudantes).order_by(Lower("first_name"), Lower("last_name"))

    context = {
        "projetos": projetos,
        "professores": professores,
        "falconis": falconis,
        # "pessoas": pessoas,
        "url": request.get_full_path(),
    }

    if data:
        context["data"] = data

    return render(request, "professores/dinamicas_view.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_editar(request, primarykey=None):
    """Edita um encontro."""

    if primarykey is None:
        return HttpResponseNotFound('<h1>Erro!</h1>')
    
    encontro = get_object_or_404(Encontro, pk=primarykey)
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax() and request.method == "POST":

        mensagem = ""
        if "atualizar" in request.POST:
            
            if ("inicio" in request.POST) and ("fim" in request.POST):

                try:
                    encontro.startDate = dateutil.parser.parse(request.POST['inicio'])
                    encontro.endDate = dateutil.parser.parse(request.POST['fim'])
                except (ValueError, OverflowError):
                    return HttpResponse("Erro com data da Dinâmica!", status=401)

                local = request.POST.get("local", None)
                if local:
                    encontro.location = local

                projeto = request.POST.get("projeto", None)
                if projeto:
                    projeto = int(projeto)
                    if projeto != 0:
                        encontro.projeto = get_object_or_404(Projeto, id=projeto)
                    else:
                        encontro.projeto = None

                facilitador = request.POST.get("facilitador", None)
                if facilitador:
                    facilitador = int(facilitador)
                    if facilitador != 0:
                        encontro.facilitador = get_object_or_404(PFEUser, id=facilitador)
                    else:
                        encontro.facilitador = None

                encontro.save()

                mensagem = "Dinâmica atualizada."
                
            else:
                return HttpResponse("Dinâmica não atualizada, erro!", status=401)

        elif "excluir" in request.POST:
            mensagem = "Mentoria excluída!"
            encontro.delete()
        else:
            return HttpResponse("Atualização não realizada.", status=401)

        context = {
            "atualizado": True,
            "mensagem": mensagem,
        }
        return JsonResponse(context)

    projetos = Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre)

    # Buscando pessoas para lista de Facilitadores
    professores_tmp = PFEUser.objects.filter(tipo_de_usuario=2)  # 'professor'
    administradores = PFEUser.objects.filter(tipo_de_usuario=4)  # 'administr'
    professores = (professores_tmp | administradores).order_by(Lower("first_name"),
                                                               Lower("last_name"))

    parceiros = PFEUser.objects.filter(tipo_de_usuario=3)
    organizacao = get_object_or_404(Organizacao, sigla="Falconi")
    falconis = parceiros.filter(parceiro__organizacao=organizacao).order_by(Lower("first_name"),
                                                                            Lower("last_name"))

    # outros_parceiros = parceiros.exclude(parceiro__organizacao=organizacao)
    # estudantes = PFEUser.objects.filter(tipo_de_usuario=1)  # (1, 'estudantes')
    # pessoas = (outros_parceiros | estudantes).order_by(Lower("first_name"),
    #                                                    Lower("last_name"))

    context = {
        "projetos": projetos,
        "professores": professores,
        "falconis": falconis,
        # "pessoas": pessoas,
        "encontro": encontro,
        "url": request.get_full_path(),
    }
    return render(request, "professores/dinamicas_view.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_lista(request):
    """Mostra os horários de dinâmicas."""

    if request.is_ajax():
        if "edicao" in request.POST:

            encontros = Encontro.objects.all().order_by("startDate")

            edicao = request.POST["edicao"]
            if edicao == "todas":
                pass  # segue com encontros
            elif edicao == "proximas":
                hoje = datetime.date.today()
                encontros = encontros.filter(startDate__gt=hoje)
            else:
                ano, semestre = map(int, edicao.split('.'))

                encontros = encontros.filter(startDate__year=ano)
                if semestre == 1:
                    encontros = encontros.filter(startDate__month__lt=8)
                else:
                    encontros = encontros.filter(startDate__month__gt=7)

            # checando se projetos atuais tem banca marcada
            configuracao = get_object_or_404(Configuracao)
            sem_dinamicas = Projeto.objects.filter(ano=configuracao.ano,
                                            semestre=configuracao.semestre)
            for encontro in encontros:
                if encontro.projeto:
                    sem_dinamicas = sem_dinamicas.exclude(id=encontro.projeto.id)

            context = {
                "sem_dinamicas": sem_dinamicas,
                "encontros": encontros,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:

        informacoes = [
            (".orientador", "orientador"),
            (".local", "local"),
            (".grupo", "grupo"),
            (".curso", "curso"),
            (".facilitador", "facilitador"),
            (".sem_agendamento", "sem agendamento"),
        ]

        edicoes, _, _ = get_edicoes(Projeto)
        context = {
                "edicoes": edicoes,
                "informacoes": informacoes,
            }

    return render(request, 'professores/dinamicas_lista.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def orientadores_tabela_completa(request):
    """Alocação dos Orientadores por semestre."""
    configuracao = get_object_or_404(Configuracao)
    orientadores = recupera_orientadores_por_semestre(configuracao)

    cabecalhos = ["Nome", "Grupos", ]
    titulo = "Alocação de Orientadores"

    context = {
        "anos": orientadores,
        "cabecalhos": cabecalhos,
        "titulo": titulo,
    }
    return render(request, 'professores/orientadores_tabela_completa.html', context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def orientadores_tabela(request):
    """Alocação dos Orientadores por semestre."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            professores_pfe = Professor.objects.all().order_by(Lower("user__first_name"),
                                                               Lower("user__last_name"))

            professores = []

            if edicao == "todas":
                professores_pfe = professores_pfe.filter(professor_orientador__isnull=False).distinct()
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    professores_pfe = professores_pfe.filter(professor_orientador__ano=ano).distinct()
                else:
                    professores_pfe = professores_pfe.filter(professor_orientador__ano=ano,
                                                             professor_orientador__semestre=semestre).distinct()

            professores = professores_pfe

            grupos = []

            for professor in professores:

                grupos_pfe = Projeto.objects.filter(orientador=professor)

                if edicao != "todas":
                    if semestre == "1/2":
                        grupos_pfe = grupos_pfe.filter(ano=ano)
                    else:
                        grupos_pfe = grupos_pfe.filter(ano=ano).\
                                                filter(semestre=semestre)


                grupos.append(grupos_pfe)

            orientacoes = zip(professores, grupos)

        context = {
            "orientacoes": orientacoes,
            "cabecalhos": ["Nome", "e-mail", "Grupos", "Projetos", ],
        }

    else:
        edicoes, _, _ = get_edicoes(Projeto, anual=True)
        titulo = "Alocação de Orientadores"
        informacoes = [
            (".semestre", "Semestre"),
            (".organizacao", "Organização"),
            (".titulo_projeto", "Título do Projeto"),
            (".tamanho_grupo", "Tamanho do Grupo"),
        ]

        context = {
            "edicoes": edicoes,
            "titulo": titulo,
            "informacoes": informacoes,
        }

    return render(request, "professores/orientadores_tabela.html", context)

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def coorientadores_tabela_completa(request):
    """Alocação dos Coorientadores por semestre."""
    configuracao = get_object_or_404(Configuracao)
    coorientadores = recupera_coorientadores_por_semestre(configuracao)

    context = {
        "anos": coorientadores,
        "cabecalhos": ["Nome", "Grupos", ],
        "titulo": "Alocação de Coorientadores",
    }
    return render(request, "professores/coorientadores_tabela_completa.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def coorientadores_tabela(request):
    """Alocação dos Coorientadores por semestre."""
    
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            professores_pfe = Professor.objects.all().order_by(Lower("user__first_name"),
                                                               Lower("user__last_name"))

            professores = []

            if edicao == "todas":
                professores_pfe = professores_pfe.filter(user__coorientador__isnull=False).distinct()
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    professores_pfe = professores_pfe.filter(user__coorientador__projeto__ano=ano).distinct()
                else:
                    professores_pfe = professores_pfe.filter(user__coorientador__projeto__ano=ano,
                                                             user__coorientador__projeto__semestre=semestre).distinct()

            professores = professores_pfe

            grupos = []

            for professor in professores:

                grupos_pfe = Coorientador.objects.filter(usuario=professor.user)

                if edicao != "todas":
                    if semestre == "1/2":
                        grupos_pfe = grupos_pfe.filter(projeto__ano=ano)
                    else:
                        grupos_pfe = grupos_pfe.filter(projeto__ano=ano).\
                                                filter(projeto__semestre=semestre)

                grupos.append(grupos_pfe)

            orientacoes = zip(professores, grupos)
    
        context = {
            "orientacoes": orientacoes,
            "cabecalhos": ["Nome", "e-mail", "Grupos", "Projetos", ],
        }

    else:
        edicoes, _, _ = get_edicoes(Projeto, anual=True)
        informacoes = [
            (".semestre", "Semestre"),
            (".organizacao", "Organização"),
            (".titulo_projeto", "Título do Projeto"),
            (".tamanho_grupo", "Tamanho do Grupo"),
        ]

        context = {
            "edicoes": edicoes,
            "titulo": "Alocação de Coorientadores",
            "informacoes": informacoes,
        }

    return render(request, "professores/coorientadores_tabela.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def avaliar_entregas(request, selecao=None):
    """Página para fzer e ver avaliação de entregas dos estudantes."""

    if selecao == "todos" and request.user.tipo_de_usuario != 4:  # Administrador
        return HttpResponse("Acesso negado.", status=401)

    if request.is_ajax():

        projetos = Projeto.objects.all().order_by("ano", "semestre")
        
        edicao = None
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao != "todas":
                ano, semestre = map(int, edicao.split('.'))
                projetos = projetos.filter(ano=ano, semestre=semestre)

        if selecao:
            if selecao != "todos":
                try:
                    projetos = projetos.filter(id=selecao)
                except:
                    return HttpResponse("Erro ao buscar projeto.", status=401)
                edicao = "nenhuma"

        else:
            projetos = projetos.filter(orientador=request.user.professor)
            

        entregas = []
        for projeto in projetos:
            composicoes = filtra_composicoes(Composicao.objects.filter(entregavel=True), projeto.ano, projeto.semestre)
            entregas.append(filtra_entregas(composicoes, projeto))

        avaliacoes = zip(projetos, entregas)

        context = {
            "avaliacoes": avaliacoes,
            "edicao": edicao,
            "prazo_avaliar": -int(get_object_or_404(Configuracao).prazo_avaliar)
        }

    else:
        
        exames = set()
        for composicao in Composicao.objects.filter(entregavel=True):
            exames.add(composicao.exame)

        configuracao = get_object_or_404(Configuracao)

        context = {
                "titulo": "Avaliar Entregas",
                "edicoes": get_edicoes(Relato)[0],
                "selecionada": "{0}.{1}".format(configuracao.ano, configuracao.semestre),
                "tipos_entregas": exames if selecao else None,
            }

    return render(request, "professores/avaliar_entregas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def relatos_quinzenais(request, todos=None):
    """Formulários com os projetos e relatos a avaliar do professor orientador."""

    if todos == "todos" and request.user.tipo_de_usuario != 4:  # Administrador
        return HttpResponse("Acesso negado.", status=401)

    if request.is_ajax():

        if "edicao" in request.POST:

            projetos = Projeto.objects.all().order_by("ano", "semestre")
            if todos != "todos":
                projetos = projetos.filter(orientador=request.user.professor)

            edicao = request.POST["edicao"]
            if edicao != "todas":
                ano, semestre = map(int, edicao.split('.'))
                projetos = projetos.filter(ano=ano, semestre=semestre)
                
            context = {
                "administracao": True,
                "projetos": projetos,
                "edicao": edicao,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:

        edicoes, _, _ = get_edicoes(Relato)
        context = {
                "titulo": "Relatos Quinzenais",
                "administracao": True,
                "edicoes": edicoes,
            }

    return render(request, "professores/relatos_quinzenais.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
@transaction.atomic
def relato_avaliar(request, projeto_id, evento_id):
    """Cria uma tela para preencher avaliações dos relatos quinzenais."""

    projeto = get_object_or_404(Projeto, pk=projeto_id)
    evento = get_object_or_404(Evento, pk=evento_id)

    evento_anterior = Evento.objects.filter(tipo_de_evento=20, endDate__lt=evento.endDate).order_by("endDate").last()
    
    alocacoes = Alocacao.objects.filter(projeto=projeto, aluno__externo__isnull=True)

    relatos = []
    for alocacao in alocacoes:
        relatos.append(Relato.objects.filter(alocacao=alocacao,
                                    momento__gt=evento_anterior.endDate + datetime.timedelta(days=1),
                                    momento__lte=evento.endDate + datetime.timedelta(days=1)).order_by("momento").last() )
                                    # O datetime.timedelta(days=1) é necessário pois temos de checar passadas 24 horas, senão vale começo do dia

    # Só o próprio orientador pode editar uma avaliação
    if projeto.orientador:
        editor = request.user == projeto.orientador.user
    else:
        editor = False

    exame = Exame.objects.get(titulo="Relato Quinzenal")

    if request.method == "POST":

        if editor:

            avaliacoes = dict(filter(lambda elem: elem[0][:3] == "op.", request.POST.items()))
            
            avaliacao_negativa = False
            for aval in avaliacoes:

                relato_id = int(aval.split('.')[1])
                relato = get_object_or_404(Relato, pk=relato_id)

                obj_nota = float(request.POST[aval])  # Seria melhor decimal.
                
                if obj_nota != relato.avaliacao:
                    relato.avaliacao = obj_nota
                    if( -0.5 < obj_nota < 0.5 ): # Para testar se zero (preciso melhorar isso)
                        avaliacao_negativa = True
                    relato.momento_avaliacao = datetime.datetime.now()
                
                feedback = request.POST.get("feedback" + str(relato.id), None)
                if feedback and feedback != "" and feedback != relato.feedback:
                    relato.feedback = feedback
                    relato.momento_avaliacao = datetime.datetime.now()
                elif feedback != relato.feedback:
                    relato.feedback = None

                relato.save()
                

            observacoes = request.POST.get("observacoes", None)

            if observacoes and observacoes != "":
                (obs, _) = Observacao.objects.get_or_create(projeto=projeto,
                                                                avaliador=request.user,
                                                                momento=evento.endDate,  # data marcada do fim do evento
                                                                exame=exame)  # (200, "Relato Quinzenal"),
                obs.observacoes_orientador = observacoes
                obs.save()
            else:
                obs = Observacao.objects.filter(projeto=projeto,
                                          avaliador=request.user,
                                          momento=evento.endDate,  # data marcada do fim do evento
                                          exame=exame).last()
                if obs:
                    obs.delete()
                

            # Dispara aviso a coordenação caso alguma observação ou estudante com dificuldade
            if avaliacao_negativa and (observacoes != ""):

                email_dest = []
                # coordenacoes = PFEUser.objects.filter(tipo_de_usuario=4)
                # for coordenador in coordenacoes:
                #     email_dest.append(str(coordenador.email))
                configuracao = get_object_or_404(Configuracao)
                email_dest.append(str(configuracao.coordenacao.user.email))
                
                email_dest.append(str(projeto.orientador.user.email))

                # Necessário refazer tabela de relatos e alocacoes para mensagens irem corretas
                relatos = []
                for alocacao in alocacoes:
                    relatos.append(Relato.objects.filter(alocacao=alocacao,
                                                momento__gt=evento_anterior.endDate + datetime.timedelta(days=1),
                                                momento__lte=evento.endDate + datetime.timedelta(days=1)).order_by("momento").last() )
                                                # O datetime.timedelta(days=1) é necessário pois temos de checar passadas 24 horas, senão valo começo do dia

                # Manda mensagem para coordenadores
                corpo_email = "<b>-- OBSERVAÇÕES DE ANOTAÇÃO QUINZENAL REALIZADA PELO PROFESSOR --</b><br>\n<br>\n"
                corpo_email += "<b>Projeto:</b> " + projeto.get_titulo() + "<br>\n"
                corpo_email += "<b>Orientador/Coorientador:</b> " + str(request.user) + "<br>\n"
                corpo_email += "<b>Grupo:</b><br>"
                for alocacao, relato in zip(alocacoes, relatos):
                    corpo_email += "&nbsp;&nbsp;&nbsp;&nbsp;\t- " + alocacao.aluno.user.get_full_name() + " (" + alocacao.aluno.get_curso_completo() + ") "
                    if relato:
                        if relato.avaliacao > 0:
                            corpo_email += "[&#x1F44D; Adequado]"
                        elif relato.avaliacao < 0:
                            corpo_email += "[<small>&#8987;</small> AGUARDANDO ORIENTADOR]"
                        else:
                            corpo_email += "[&#x1F44E; Inadequado]"
                    else:
                        corpo_email += "[<small>&#10060;</small> NÃO ENTREGUE POR ESTUDANTE]"
                    corpo_email += "<br>"
                corpo_email += "<hr>"
                corpo_email += "<b>Observações:</b><br>\n" 
                corpo_email += "<div style='padding: 10px; border: 2px solid #DDDDDD;'>" + htmlizar(observacoes) + "</div><br>\n"
                email("Observações de Anotação Quinzenal Realizada pelo professor", email_dest, corpo_email)

            context = {
                "area_principal": True,
                "mensagem": "avaliação realizada",
            }
            return render(request, "generic.html", context=context)
            
        else:
            return HttpResponseNotFound("<h1>Erro na edição do relato!</h1>")

    else:  # GET

        obs = Observacao.objects.filter(projeto=projeto,
                                        momento__gt=evento_anterior.endDate + datetime.timedelta(days=1),
                                        momento__lte=evento.endDate + datetime.timedelta(days=1),
                                        exame=exame).last()  # (200, "Relato Quinzenal"),
                                        # O datetime.timedelta(days=1) é necessário pois temos de checar passadas 24 horas, senão vale começo do dia

        context = {
            "editor": editor,
            "projeto": projeto,
            "observacoes": obs.observacoes_orientador if obs else None,
            "alocacoes_relatos": zip(alocacoes, relatos),
            "evento": evento,
            "Observacao": Observacao,
            "Relato": Relato,

        }
        return render(request, "professores/relato_avaliar.html", context=context)


# Criei esse função temporária para tratar caso a edição seja passada diretamente na URL
def resultado_projetos_intern(request, ano=None, semestre=None, professor=None):
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            projetos = Projeto.objects.all()

            if edicao != "todas":
                ano, semestre = edicao.split('.')
                projetos = projetos.filter(ano=ano, semestre=semestre)

            show_orientador = True
            if professor is not None:
                # Incluindo também se coorientação
                coorientacoes = Coorientador.objects.filter(usuario=professor.user).values_list("projeto", flat=True)
                projetos_ori = projetos.filter(orientador=professor)
                projetos_coori = projetos.filter(id__in=coorientacoes)
                projetos = projetos_ori | projetos_coori
                if projetos_coori.count() == 0:
                    show_orientador = False

            relatorio_preliminar = []
            relatorio_intermediario = []
            relatorio_final = []
            banca_intermediaria = []
            banca_final = []
            banca_falconi = []

            for projeto in projetos:

                alocacoes = Alocacao.objects.filter(projeto=projeto)
                
                if alocacoes:

                    primeira = alocacoes.first()
                    medias = primeira.get_media

                    if ("peso_grupo_inter" in medias) and (medias["peso_grupo_inter"] is not None) and (medias["peso_grupo_inter"] > 0):
                        nota = medias["nota_grupo_inter"]/medias["peso_grupo_inter"]
                        relatorio_intermediario.append({"conceito": "{0}".format(converte_letra(nota, espaco="&nbsp;")),
                                                "nota_texto": "{0:5.2f}".format(nota),
                                                "nota": nota})                    
                    else:
                        relatorio_intermediario.append({"conceito": "&nbsp;-&nbsp;",
                                                    "nota_texto": "",
                                                    "nota": 0})

                    if ("peso_grupo_final" in medias) and (medias["peso_grupo_final"] is not None) and (medias["peso_grupo_final"] > 0):
                        nota = medias["nota_grupo_final"]/medias["peso_grupo_final"]
                        relatorio_final.append({"conceito": "{0}".format(converte_letra(nota, espaco="&nbsp;")),
                                                "nota_texto": "{0:5.2f}".format(nota),
                                                "nota": nota})                    
                    else:
                        relatorio_final.append({"conceito": "&nbsp;-&nbsp;",
                                                    "nota_texto": "",
                                                    "nota": 0})
 

                else:
                    relatorio_intermediario.append(("&nbsp;-&nbsp;", None, 0))
                    relatorio_final.append(("&nbsp;-&nbsp;", None, 0))

                exame = Exame.objects.get(titulo="Banca Final")
                aval_banc_final = Avaliacao2.objects.filter(projeto=projeto, exame=exame)  # B. Final
                nota_banca_final, peso, avaliadores = Aluno.get_banca(None, aval_banc_final, eh_banca=True)
                if peso is not None:
                    banca_final.append({"conceito": "{0}".format(converte_letra(nota_banca_final, espaco="&nbsp;")),
                                                "nota_texto": "{0:5.2f}".format(nota_banca_final),
                                                "nota": nota_banca_final})                    
                else:
                    banca_final.append({"conceito": "&nbsp;-&nbsp;",
                                                "nota_texto": "",
                                                "nota": 0})


                exame = Exame.objects.get(titulo="Banca Intermediária")
                aval_banc_interm = Avaliacao2.objects.filter(projeto=projeto, exame=exame)  # B. Int.
                nota_banca_intermediaria, peso, avaliadores = Aluno.get_banca(None, aval_banc_interm, eh_banca=True)
                if peso is not None:
                    banca_intermediaria.append({"conceito": "{0}".format(converte_letra(nota_banca_intermediaria, espaco="&nbsp;")),
                                                "nota_texto": "{0:5.2f}".format(nota_banca_intermediaria),
                                                "nota": nota_banca_intermediaria})                    
                else:
                    banca_intermediaria.append({"conceito": "&nbsp;-&nbsp;",
                                                "nota_texto": "",
                                                "nota": 0})
                    

                exame = Exame.objects.get(titulo="Falconi")
                aval_banc_falconi = Avaliacao2.objects.filter(projeto=projeto, exame=exame)  # Falc.
                nota_banca_falconi, peso, avaliadores = Aluno.get_banca(None, aval_banc_falconi)
                if peso is not None:
                    nomes = ""
                    for nome in avaliadores:
                        nomes += "&#8226; "+str(nome)+"<br>"

                    certificacao = ""
                    if nota_banca_falconi >= 8:
                        certificacao = "E"  # Excelencia FALCONI-INSPER
                    elif nota_banca_falconi >= 6:
                        certificacao = "D"  # Destaque FALCONI-INSPER

                    banca_falconi.append({"avaliadores": "{0}".format(nomes),
                                          "nota_texto": "{0:5.2f}".format(nota_banca_falconi),
                                          "nota": nota_banca_falconi,
                                          "certificacao": certificacao})
                    
                else:
                    banca_falconi.append({"avaliadores": "&nbsp;-&nbsp;",
                                          "nota_texto": "",
                                          "nota": 0,
                                          "certificacao": ""})

            tabela = zip(projetos,
                         relatorio_intermediario,
                         relatorio_final,
                         banca_intermediaria,
                         banca_final,
                         banca_falconi)

            context = {
                    "tabela": tabela,
                    "edicao": edicao,
                    "show_orientador": show_orientador,
                }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:
        edicoes, _, _ = get_edicoes(Projeto)

        if ano and semestre:
            selecionada = str(ano) + "." + str(semestre)
        else:
            selecionada = None

        informacoes = [
            ("#ProjetosTable tr > *:nth-child(2)", "Período"),
            ("#ProjetosTable tr > *:nth-child(3)", "Orientador"),
            ("""#ProjetosTable tr > *:nth-child(4),
                #ProjetosTable tr > *:nth-child(5),
                #ProjetosTable tr > *:nth-child(6),
                #ProjetosTable tr > *:nth-child(7),
                #ProjetosTable tr > *:nth-child(8)""", "Notas"),
            (".grupo", "Grupo"),
            (".email", "e-mail", "grupo"),
            (".curso", "curso", "grupo"),
        ]

        context = {
            "titulo": "Resultado dos Projetos",
            "edicoes": edicoes,
            "selecionada": selecionada,
            "informacoes": informacoes,
        }

    return render(request, "professores/resultado_projetos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def resultado_projetos_edicao(request, edicao):
    """Mostra os resultados das avaliações (Bancas) para uma edição."""
    try:
        ano, semestre = map(int, edicao.split('.'))
    except ValueError:
        return HttpResponseNotFound("<h1>Erro em identificar ano e semestre!</h1>")
    return resultado_projetos_intern(request, ano, semestre)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def resultado_projetos(request):
    """Mostra os resultados das avaliações (Bancas)."""
    return resultado_projetos_intern(request)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def resultado_meus_projetos(request):
    """Mostra os resultados das avaliações somente do professor (Bancas)."""
    return resultado_projetos_intern(request, professor=request.user.professor)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def todos_professores(request):
    """Exibe todas os professores que estão cadastrados."""
    context = {
        "professores": Professor.objects.all(),
        "cabecalhos": ["Nome", "e-mail", "Bancas", "Orientações", "Lattes", ],
        "titulo": "Professores",
        }

    return render(request, "professores/todos_professores.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def objetivo_editar(request, primarykey):
    """Edita um objetivo de aprendizado."""
    objetivo = get_object_or_404(ObjetivosDeAprendizagem, pk=primarykey)

    if request.method == "POST":
        # if editar_objetivo(objetivo, request):
        #     mensagem = "Banca editada."
        # else:
        #     mensagem = "Erro ao Editar banca."
        context = {
            "area_principal": True,
            "bancas_index": True,
            # "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    context = {"objetivo": objetivo,}
    return render(request, "professores/objetivo_editar.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def objetivos_rubricas(request):
    """Exibe os objetivos e rubricas."""
    context = {
        "titulo": "Objetivos de Aprendizagem e Rubricas",
        "objetivos": get_objetivos_atuais(ObjetivosDeAprendizagem.objects.all()), 
    }
    return render(request, "professores/objetivos_rubricas.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def ver_pares(request, alocacao_id, momento):
    """Permite visualizar a avaliação de pares."""

    # DEIXANDO DE USAR PARA USAR ver_pares_projeto #

    alocacao_de = get_object_or_404(Alocacao, pk=alocacao_id)

    if request.user != alocacao_de.projeto.orientador.user and request.user.tipo_de_usuario != 4:
        return HttpResponse("Somente o próprio orientador pode confirmar uma avaliação de pares.", status=401)

    if request.method == "POST":
        if momento=="intermediaria" and not alocacao_de.avaliacao_intermediaria:
            alocacao_de.avaliacao_intermediaria = datetime.datetime.now()
        elif momento=="final" and not alocacao_de.avaliacao_final:
            alocacao_de.avaliacao_final = datetime.datetime.now()
        alocacao_de.save()
        return redirect("/professores/avaliacoes_pares/")

    tipo = 0 if momento=="intermediaria" else 1
    
    alocacoes = Alocacao.objects.filter(projeto=alocacao_de.projeto).exclude(aluno=alocacao_de.aluno)
    
    pares = []
    for alocacao in alocacoes:
        par = Pares.objects.filter(alocacao_de=alocacao_de, alocacao_para=alocacao, tipo=tipo).first()
        pares.append(par)

    colegas = zip(alocacoes, pares)

    configuracao = get_object_or_404(Configuracao)

    context = {
        "estudante": alocacao_de.aluno,
        "colegas": colegas,
        "momento": momento,
        "projeto": alocacao_de.projeto,
        "configuracao": configuracao,
    }

    return render(request, "professores/ver_pares.html", context)



@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def ver_pares_projeto(request, projeto_id, momento):
    """Permite visualizar a avaliação de pares."""

    projeto = get_object_or_404(Projeto, pk=projeto_id)
    alocacoes = Alocacao.objects.filter(projeto=projeto)

    if request.user != projeto.orientador.user and request.user.tipo_de_usuario != 4:
        return HttpResponse("Somente o próprio orientador pode confirmar uma avaliação de pares.", status=401)

    if request.user == projeto.orientador.user:
        for alocacao in alocacoes:
            if momento=="intermediaria" and not alocacao.avaliacao_intermediaria:
                alocacao.avaliacao_intermediaria = datetime.datetime.now()
            elif momento=="final" and not alocacao.avaliacao_final:
                alocacao.avaliacao_final = datetime.datetime.now()
            alocacao.save()

    tipo = 0 if momento=="intermediaria" else 1
        
    pares = []
    for alocacao in alocacoes:
        par = Pares.objects.filter(alocacao_de__projeto=projeto, alocacao_para=alocacao, tipo=tipo)
        pares.append(par)

    colegas = zip(alocacoes, pares)

    configuracao = get_object_or_404(Configuracao)

    entregas = [
        "Entregou muito abaixo de esperado, colocando a entrega em risco e obrigando outro(s) membro(s) a mudarem planejamentos pessoais para garanti-la.",
        "Entregou abaixo do esperado.",
        "Entregou precisamente o esperado.",
        "Entregou acima do esperado.",
        "Entregou muito acima do esperado, mudando planejamentos pessoais para garantir uma entrega que estava em risco.",
    ]

    iniciativas = [
        "Mesmo quando lembrado, não cumpriu as tarefas designadas.",
        "Precisou ser lembrado, mas cumpriu as tarefas designadas.",
        "Autonomamente, cumpriu as tarefas designadas, nem mais nem menos.",
        "Além de cumprir as tarefas designadas, ajudou outro(s) membro(s) que estavam tendo dificuldades.",
        "Monopolizou parte das tarefas, assumindo tarefas de outro(s) membro(s) mesmo quando não havia evidência de dificuldades.",
    ]

    comunicacoes = [
        "Teve dificuldades, nunca as comunicou e ao final elas impediram a entrega.",
        "Teve dificuldades e nunca as comunicou, mas pelo menos não impediram a entrega.",
        "Aparentemente não teve dificuldades, mas nunca reportou nada.",
        "Comunicou dificuldades. Independente da entrega ter sido feita ou não, a equipe não foi surpreendida.",
        "Apesar de não ter dificuldades, estava sempre reportando como estava indo.",
    ]

    context = {
        "alocacoes": alocacoes,
        "colegas": colegas,
        "momento": momento,
        "projeto": projeto,
        "configuracao": configuracao,
        "entregas": entregas,
        "iniciativas": iniciativas,
        "comunicacoes": comunicacoes,
    }

    return render(request, "professores/ver_pares_projeto.html", context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def planos_de_orientacao(request):
    """Mostra os planos de orientação do professor."""
    projetos = Projeto.objects.filter(orientador=request.user.professor)\
        .order_by("-ano", "-semestre")

    tipo = TipoDocumento.objects.get(sigla="TPO")  # Template de Plano de Orientação
    template = Documento.objects.filter(tipo_documento=tipo).last()

    context = {
        "titulo": "Planos de Orientação",
        "projetos": projetos,
        "configuracao": get_object_or_404(Configuracao),
        "template": template,
    }
    return render(request, "professores/planos_de_orientacao.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def planos_de_orientacao_todos(request):
    """Formulários com os projetos e planos de orientação dos professores orientadores."""
    usuario_sem_acesso(request, (4,)) # Soh Parc Adm

    if request.is_ajax():

        if "edicao" in request.POST:

            projetos = Projeto.objects.all()

            edicao = request.POST["edicao"]
            if edicao != "todas":
                ano, semestre = edicao.split('.')
                projetos = projetos.filter(ano=ano, semestre=semestre)
                
            context = {
                "administracao": True,
                "projetos": projetos,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:
        context = {
                "titulo": "Planos de Orientação",
                "administracao": True,
                "edicoes": get_edicoes(Projeto)[0],
            }

    return render(request, "professores/planos_de_orientacao_todos.html", context=context)
