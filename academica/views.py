#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 10 de Abril de 2023
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_academica(request):
    """Mostra página principal da área acadêmica do sistema."""
    context = {"titulo": "Área Acadêmica",}

    if "/academica/academica" in request.path:
        return render(request, "academica/academica.html", context=context)
    else:
        return render(request, "academica/index_academica.html", context=context)
    
