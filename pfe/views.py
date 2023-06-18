#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2023
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse


@login_required
def index(request):
    """Página principal do sistema do Projeto Final de Engenharia."""
    # num_visits = request.session.get('num_visits', 0) # Visitas a página.
    # request.session['num_visits'] = num_visits + 1
    return render(request, 'index.html')


def manutencao(request):
    """Página de Manutenção do Projeto Final de Engenharia."""
    return render(request, 'manutencao.html')

from django.contrib.auth.models import Group
from users.models import PFEUser

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Feito"

    adm_group = Group.objects.get(name="Administrador")
    est_group = Group.objects.get(name="Estudante")
    parc_group = Group.objects.get(name="Parceiro")
    prof_group = Group.objects.get(name="Professor")

    # TIPO_DE_USUARIO_CHOICES = (
    #     (1, 'aluno'),
    #     (2, 'professor'),
    #     (3, 'parceiro'),
    #     (4, 'administrador'),
    # )

    users = PFEUser.objects.all()
    for user in users:
        if user.tipo_de_usuario == 1:
            user.groups.add(est_group)
        elif user.tipo_de_usuario == 2:
            user.groups.add(prof_group)
        elif user.tipo_de_usuario == 3:
            user.groups.add(parc_group)
        elif user.tipo_de_usuario == 4:
            user.groups.add(adm_group)

    return HttpResponse(message)