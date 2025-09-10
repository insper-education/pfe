#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 10 de Setembro de 2025
"""

import logging

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404

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

