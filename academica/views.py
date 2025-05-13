#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 10 de Abril de 2023
"""


from datetime import timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.http import HttpResponse

from estudantes.models import Relato, Pares
from projetos.models import Evento

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
