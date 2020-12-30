#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 29 de Dezembro de 2020
"""

from django.shortcuts import render

from django.contrib.auth.decorators import login_required, permission_required

# Create your views here.


@login_required
@permission_required("users.altera_professor", login_url='/')
def index_operacional(request):
    """Mostra página principal para equipe operacional."""

    return render(request, 'operacional/index_operacional.html')
