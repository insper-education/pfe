#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 30 de Novembro de 2025
"""

import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from projetos.models import Banca, Encontro, Configuracao, TematicaEncontro
from users.models import PFEUser


# @login_required
# @permission_required("users.altera_professor", raise_exception=True)
# Permite que compartilhe com a agenda mesmo com pessoas não logadas
def ajax_bancas(request):
    """Retorna as bancas do ano."""

    if request.headers.get("X-Requested-With") != "XMLHttpRequest" or request.method != "POST":
        return HttpResponse("Erro.", status=401)

    if "start" not in request.POST or "end" not in request.POST:
        return HttpResponse("Erro.", status=401)

    start = datetime.datetime.strptime(request.POST["start"], "%Y-%m-%d").date() - datetime.timedelta(days=90)
    end = datetime.datetime.strptime(request.POST["end"], "%Y-%m-%d").date() + datetime.timedelta(days=90)
    bancas = {}

    for banca in Banca.objects.filter(startDate__gte=start, startDate__lte=end):
        projeto = banca.get_projeto()
        orientador = projeto.orientador.user.get_full_name() if projeto and projeto.orientador else None
        organizacao_sigla = projeto.organizacao.sigla if projeto and projeto.organizacao else None
        estudante = banca.alocacao.aluno.user.get_full_name() if banca.alocacao else None
        membros = banca.membros()
        if request.user.is_authenticated and request.user.eh_prof_a:
            editable = request.user.eh_admin or (projeto and projeto.orientador == request.user.professor)
        else:
            editable = False

        title = f"{projeto.get_titulo_org()}" if projeto else "Projeto ou alocação não identificados"
        if banca.alocacao:
            title = f"Estudante: {estudante} - {projeto.get_titulo_org()}"
        if banca.location:
            title += f"\n<br>Local: {banca.location}"
        title += "\n<br>Banca:"
        for membro in membros:
            title += f"\n<br>&bull; {membro.get_full_name()}"
            if projeto.orientador and projeto.orientador.user == membro:
                title += " (O)"

        if banca.composicao and banca.composicao.exame:
            cor = banca.composicao.exame.cor
            className = banca.composicao.exame.className
        else:
            cor = "808080"
            className = ""

        bancas[banca.id] = {
            "start": banca.startDate.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": banca.endDate.strftime("%Y-%m-%dT%H:%M:%S"),
            "local": banca.location,
            "organizacao": organizacao_sigla,
            "orientador": orientador,
            "estudante": estudante,
            "color": f"#{cor}",
            "className": className,
            "editable": editable,
            "title": title,
            **{f"membro{num+1}": membro.get_full_name() for num, membro in enumerate(membros)}
        }

    return JsonResponse(bancas)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def ajax_atualiza_banca(request):
    """Atualiza os dados de uma banca por ajax."""
    if request.headers.get("X-Requested-With") != "XMLHttpRequest" or request.method != "POST":
        return HttpResponse("Erro.", status=400)
    if not all(key in request.POST for key in ("id", "start", "end")):
        return HttpResponse("Erro.", status=400)

    try:
        banca = Banca.objects.get(id=request.POST["id"])
        banca.startDate = datetime.datetime.strptime(request.POST["start"], "%d/%m/%Y, %H:%M")
        banca.endDate = datetime.datetime.strptime(request.POST["end"], "%d/%m/%Y, %H:%M")
        banca.save()
        return JsonResponse({"atualizado": True})
    except Banca.DoesNotExist:
        return HttpResponse("Banca não encontrada", status=404)
    except ValueError:
        return HttpResponse("Formato de data inválido", status=400)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def ajax_atualiza_dinamica(request):
    """Atualiza os dados de uma dinamica por ajax."""

    if request.headers.get("X-Requested-With") != "XMLHttpRequest" or request.method != "POST":
        return HttpResponse("Erro.", status=400)
    if not all(key in request.POST for key in ("id", "start", "end")):
        return HttpResponse("Erro.", status=400)

    try:
        encontro = Encontro.objects.get(id=request.POST["id"])
        encontro.startDate = datetime.datetime.strptime(request.POST["start"], "%d/%m/%Y, %H:%M")
        encontro.endDate = datetime.datetime.strptime(request.POST["end"], "%d/%m/%Y, %H:%M")
        encontro.save()
        return JsonResponse({"atualizado": True})
    except Encontro.DoesNotExist:
        return HttpResponse("Encontro não encontrado", status=404)
    except ValueError:
        return HttpResponse("Formato de data inválido", status=400)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def ajax_permite_agendar_mentorias(request):
    """Atualiza uma configuração de agendamento de mentorias."""

    if request.headers.get("X-Requested-With") != "XMLHttpRequest" or request.method != "POST":
        return HttpResponse("Erro não identificado.", status=401)

    configuracao = get_object_or_404(Configuracao)
    configuracao.permite_agendar_mentorias = request.POST.get("permite_agendar_mentorias") == "true"
    configuracao.save()
    return JsonResponse({"atualizado": True})


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def ajax_atualiza_visibilidade_tematica(request):
    """Atualiza uma configuração de visibilidade de temáticas de mentorias."""

    if request.headers.get("X-Requested-With") != "XMLHttpRequest" or request.method != "POST":
        return HttpResponse("Erro não identificado.", status=401)
    
    tematica_id = request.POST.get("tematica_id", None)
    visibilidade = request.POST.get("visibilidade", None)
    if tematica_id and visibilidade is not None:
        try:
            tematica = get_object_or_404(TematicaEncontro, pk=int(tematica_id))
        except ValueError:
            return HttpResponse("Temática não encontrada.", status=404)
        tematica.visibilidade = True if visibilidade == "true" else False
        tematica.save()
        return JsonResponse({"atualizado": True})


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def ajax_verifica_membro_banca(request):
    """Verifica se o usuário é membro de alguma banca."""
    membro_id = request.POST.get("membro_id", None)
    edicao = request.POST.get("edicao", None)
    tipo = [request.POST.get("tipo", None)]  # "BI", "BF", "P", "F"
    remove_banca = request.POST.get("remove_banca", None)
    
    if request.headers.get("X-Requested-With") != "XMLHttpRequest" or request.method != "POST":
        return HttpResponse("Erro não identificado.", status=401)
    if not membro_id or not tipo:
        return JsonResponse({"lista_bancas": []})
    
    try:
        membro = get_object_or_404(PFEUser, pk=int(membro_id))
    except ValueError:
        return HttpResponse("Membro não encontrado.", status=404)
    
    bancas = Banca.get_bancas_com_membro(membro, siglas=tipo)

    if edicao and '.' in edicao:
        ano, semestre = edicao.split('.')
        bancas = bancas.filter(projeto__ano=ano, projeto__semestre=semestre)
    else:
        configuracao = get_object_or_404(Configuracao)
        bancas = bancas.filter(projeto__ano=configuracao.ano, projeto__semestre=configuracao.semestre)
    
    # Para não contar a própria banca que está sendo editada
    if remove_banca:
        remove_banca = int(remove_banca)
        bancas = bancas.exclude(id=remove_banca)

    lista_bancas = []
    for banca in bancas:
        if banca.alocacao:
            aluno_nome = banca.alocacao.aluno.user.get_full_name()
            aluno_email = banca.alocacao.aluno.user.email
            projeto_titulo = banca.alocacao.projeto.get_titulo_org()
        else:
            aluno_nome = ""
            aluno_email = ""
            projeto_titulo = banca.projeto.get_titulo_org() if banca.projeto else ""
        data = banca.startDate.strftime("%d/%m %H:%M") if banca.startDate else ""
        data += " às " + banca.endDate.strftime("%H:%M") if banca.endDate else ""
        lista_bancas.append({
            "id": banca.id,
            "data": data,
            "tipo": banca.composicao.exame.titulo if banca.composicao and banca.composicao.exame else "",
            "projeto": projeto_titulo,
            "aluno_nome": aluno_nome,
            "aluno_email": aluno_email,
            "local": banca.location if banca.location else "",
            "link": banca.link if banca.link else "",
        })

    return JsonResponse({"lista_bancas": lista_bancas})
