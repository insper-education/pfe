#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 10 de Abril de 2023
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from administracao.support import usuario_sem_acesso

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_academica(request):
    """Mostra página principal do usuário professor."""   
    v = usuario_sem_acesso(request, (2, 4,))
    if v: return v  # Prof, Adm
    return render(request, 'academica/index_academica.html')
