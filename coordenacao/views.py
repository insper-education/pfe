#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 10 de Setembro de 2025
"""

import logging
from os import link

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse

from projetos.models import Evento

# Get an instance of a logger
logger = logging.getLogger("django")


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_coordenacao(request):
    """Mostra página principal do usuário coordenador."""

    context = {
        "titulo": {"pt": "Área da Coordenação", "en": "Coordination Area"},
    }
    if "/coordenacao/coordenacao" in request.path:
        return render(request, "coordenacao/coordenacao.html", context=context)
    else:
        return render(request, "coordenacao/index_coordenacao.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def edita_aula(request, primarykey=None):
    """Mostra página para editar uma aula."""

    if primarykey is None or not request.user.eh_admin:
        return HttpResponse("Erro", status=401)
    
    evento = get_object_or_404(Evento, pk=primarykey)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" and request.method == "POST": # Ajax check
        evento.questao_problema_desafio = request.POST.get("questao_problema_desafio", "").strip()
        evento.atividade = request.POST.get("atividade", "").strip()
        evento.evidencias_de_aprendizado = request.POST.get("evidencias_de_aprendizado", "").strip()
        evento.descricao = request.POST.get("descricao", "").strip()
        evento.save()
        return JsonResponse({"atualizado": True,})
        
    context = {
        "Evento": Evento,
        "evento": evento,
        "url": request.get_full_path(),
    }
    return render(request, "coordenacao/edita_aula.html", context)
