#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 10 de Abril de 2023
"""


from datetime import timedelta
import datetime
import math

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from estudantes.models import Relato, Pares
from projetos.models import Evento, Area, Projeto, Configuracao, Documento, Desconto

from operacional.models import Curso

from users.models import Alocacao, Aluno
from users.support import get_edicoes


@login_required
def index_academica(request):
    """Mostra página principal da área acadêmica do sistema."""
    if not (request.user.has_perm("users.altera_professor") or request.user.has_perm("projetos.view_avaliacao2")):
        raise PermissionDenied
    context = {"titulo": {"pt": "Área Acadêmica", "en": "Academic Area"},}
    if "/academica/academica" in request.path:
        return render(request, "academica/academica.html", context=context)
    else:
        return render(request, "academica/index_academica.html", context=context)
    

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_grupos(request):
    """Mostra página com as dinâmicas de grupos."""
    if request.is_ajax():
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        
        if request.POST["edicao"] != "todas":
            ano, semestre = map(int, request.POST["edicao"].split('.'))
            alocacoes = Alocacao.objects.filter(projeto__ano=ano, projeto__semestre=semestre)
        else:
            alocacoes = Alocacao.objects.all()
            ano, semestre = None, None

        informacoes = []

        if ano and semestre:
            eventos_rq = Evento.get_eventos(sigla="RQ", ano=ano, semestre=semestre)
            qt = len(eventos_rq)
        
        for alocacao in alocacoes:

            if not ano or not semestre:
                eventos_rq = Evento.get_eventos(sigla="RQ", ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)
                qt = len(eventos_rq)

            # Parte dos relatos quinzenais
            qr = 0
            qa = 0
            for index, evento in enumerate(eventos_rq):
                if index == 0:
                    relato = Relato.objects.filter(
                        alocacao=alocacao,
                        momento__lte=evento.endDate + timedelta(days=1)
                    ).order_by("momento").last()
                else:
                    relato = Relato.objects.filter(
                        alocacao=alocacao,
                        momento__gt=eventos_rq[index-1].endDate + timedelta(days=1),
                        momento__lte=evento.endDate + timedelta(days=1)
                    ).order_by("momento").last()

                if relato:
                    qr += 1
                    if relato.avaliacao > 0:
                        qa += 1

            quinzenais_adequados = f"{round(100*qa/qr) if qr else 0}%"
            quinzenais_realizados = f"{round(100*qr/qt) if qt else 0}%"

            # Parte das avaliações de pares
            pares = {"i": {}, "f": {}}
            for tipo in [0, 1]:
                
                pares_entrega = 0
                pares_iniciativa = 0
                pares_comunicacao = 0
                pars = Pares.objects.filter(alocacao_para=alocacao, tipo=tipo)  # (0, "intermediaria"),   # (1, "final")
                qp = len(pars)
                for par in pars:
                    pares_entrega += par.entrega if par.entrega else 0
                    pares_iniciativa += par.iniciativa if par.iniciativa else 0
                    pares_comunicacao += par.comunicacao if par.comunicacao else 0

                pares["f" if tipo==1 else "i"] = {
                    "entrega": f"{round(pares_entrega/qp,2) if qp else 0}",
                    "iniciativa": f"{round(pares_iniciativa/qp,2) if qp else 0}",
                    "comunicacao": f"{round(pares_comunicacao/qp,2) if qp else 0}",
                }

            informacoes.append([alocacao, quinzenais_realizados, quinzenais_adequados, pares])


        cabecalhos = [{"pt": "Nome", "en": "Name"},
                        {"pt": "e-mail", "en": "e-mail"},
                        {"pt": "Curso", "en": "Program"},
                        {"pt": "Projeto", "en": "Project"},
                        {"pt": "Quinzenal Realizado", "en": "Biweekly Completed"},
                        {"pt": "Quinzenal Adequado", "en": "Biweekly Adequate"},
                        {"pt": "Pares Int. Entrega", "en": "Int. Pairs Delivery"},
                        {"pt": "Pares Int. Iniciativa", "en": "Int. Pairs Initiative"},
                        {"pt": "Pares Int. Comunicação", "en": "Int. Pairs Communication"},
                        {"pt": "Pares Fin. Entrega", "en": "Fin. Pairs Delivery"},
                        {"pt": "Pares Fin. Iniciativa", "en": "Fin. Pairs Initiative"},
                        {"pt": "Pares Fin. Comunicação", "en": "Fin. Pairs Communication"},
                        ]
        
        captions = []
        for curso in Curso.objects.filter(curso_do_insper=True).order_by("id"):
            captions.append({
                "sigla": curso.sigla_curta,
                "pt": curso.nome,
                "en": curso.nome_en,
            })

        context = {
            "informacoes": informacoes,
            "cabecalhos": cabecalhos,
            "captions": captions,
            "Pares": Pares,
        }

    else:
        context = {
            "titulo": {"pt": "Dinâmicas de Grupos", "en": "Group Dynamics"},
            "edicoes": get_edicoes(Aluno)[0],
            }

    return render(request, "academica/dinamicas_grupos.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_areas_interesse(request):
    """Mostra tabela com as possíveis áreas de interesse."""
    
    cabecalhos = [
        {"pt": "Área", "en": "Area"},
        {"pt": "Descrição", "en": "Description"}, 
    ]

    context = {
        "titulo": {"pt": "Lista de Áreas de Interesse", "en": "Areas of Interest List"},
        "cabecalhos": cabecalhos,
        "areas": Area.objects.filter(ativa=True),
    }

    return render(request, "academica/lista_areas_interesse.html", context)


def lanca_descontos(ano=None, semestre=None):
    """Lança os descontos para os estudantes de acordo com as regras definidas."""

    if ano is None or semestre is None:
        configuracao = get_object_or_404(Configuracao)
        ano, semestre = configuracao.ano, configuracao.semestre

    hoje = datetime.date.today()
    projetos = Projeto.objects.filter(ano=ano, semestre=semestre)
    eventos = {
        "erp": Evento.get_evento(sigla="ERP", ano=ano, semestre=semestre),  # Entrega de Relatório Preliminar (Grupo)
        "api": Evento.get_evento(sigla="API", ano=ano, semestre=semestre),  # Avaliação de Pares Intermediária
        "apf": Evento.get_evento(sigla="APF", ano=ano, semestre=semestre),  # Avaliação de Pares Final
        "rqs": Evento.get_eventos(sigla="RQ", ano=ano, semestre=semestre),  # Relatos Quinzenais
        "pas": Evento.get_evento(sigla="PAS", ano=ano, semestre=semestre),  # Preenchimento de Alocação Semanal
    }

    descontos = []

    def add_desconto(obj, evento, nota):
        desconto, _ = Desconto.objects.get_or_create(**obj, evento=evento)
        desconto.nota = nota
        desconto.save()
        descontos.append(desconto)
    
    for projeto in projetos:

        # Verifica se o relatório preliminar foi entregue
        if eventos["erp"]:
            relatorioPreliminar = Documento.objects.filter(projeto=projeto, tipo_documento__sigla="RPR").last()
            data_entrega = relatorioPreliminar.data.date() if relatorioPreliminar else hoje
            atraso_dias = (data_entrega - eventos["erp"].endDate).days
            semanas_atraso = math.ceil(atraso_dias / 7)
            if semanas_atraso > 0:
                add_desconto({"projeto": projeto}, eventos["erp"], 0.5 * semanas_atraso)

        for alocacao in Alocacao.objects.filter(projeto=projeto, aluno__externo__isnull=True):

            # Avaliação de Pares (Intermediária e Final)
            for tipo, evento_key in [(0, "api"), (1, "apf")]:
                evento = eventos[evento_key]
                if evento and hoje > evento.endDate:
                    if not Pares.objects.filter(alocacao_de=alocacao, tipo=tipo).exists():
                        add_desconto({"alocacao": alocacao}, evento, 0.5)
        
            # Relato Quinzenal
            evento_anterior = None
            for evento in eventos["rqs"]:
                if hoje > evento.endDate:
                    if evento_anterior:
                        if not Relato.objects.filter(alocacao=alocacao, momento__date__gt=evento_anterior.endDate, momento__date__lte=evento.endDate).exists():
                            add_desconto({"alocacao": alocacao}, evento, 0.25)
                    else:
                        if not Relato.objects.filter(alocacao=alocacao, momento__date__lte=evento.endDate).exists():
                            add_desconto({"alocacao": alocacao}, evento, 0.25)
                evento_anterior = evento

            # Planejamento de Alocação Semanal
            if eventos["pas"] and hoje > eventos["pas"].endDate:
                agendado_horarios = alocacao.agendado_horarios.date() if alocacao.agendado_horarios else hoje
                atraso_dias = (agendado_horarios - eventos["pas"].endDate).days
                semanas_atraso = math.ceil(atraso_dias / 7)
                if semanas_atraso > 0:
                    add_desconto({"alocacao": alocacao}, eventos["pas"], 0.25 * semanas_atraso)

    return descontos


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def descontos(request):
    """Mostra tabela com os possíveis descontos."""
    configuracao = get_object_or_404(Configuracao)
    ano, semestre = configuracao.ano, configuracao.semestre
    descontos = lanca_descontos(ano, semestre)

    context = {
        "titulo": {"pt": "Lista de Descontos", "en": "Discounts List"},
        "descontos": descontos,
    }

    return render(request, "academica/descontos.html", context)

