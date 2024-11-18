#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2023
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse


@login_required
def index_old(request):
    """Antiga Página principal do sistema."""
    return render(request, "index_old.html")

#@login_required
def index(request):
    """Página principal do sistema."""
    if request.user.is_authenticated:
        return render(request, "index.html")
    else:
        return render(request, "info.html")

def info(request):
    """Página com informações."""
    return render(request, "info.html")

def manutencao(request):
    """Página de Manutenção do sistema."""
    return render(request, "manutencao.html")

def custom_400(request, exception):
    mensagem = "<h1>Bad Request (400)</h1>"
    if (exception):
        mensagem += str(exception) + "<br>"
    mensagem += "Em caso de dúvida " + settings.CONTATO
    #t = loader.get_template("400.html")
    #t.render(Context({"exception_value": value,})
    return HttpResponse(mensagem)


from projetos.models import Configuracao, Organizacao, Proposta, Projeto
@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Feito"

    propostas = Proposta.objects.filter(disponivel=True)
    for proposta in propostas:
        proposta.habilidades = True
        proposta.design = True
        proposta.realistico = True
        proposta.normas = True
        proposta.restricoes = True
        proposta.experimentacao = True
        proposta.equipe = True
        proposta.duracao = True
        proposta.carga = True
        proposta.mensuravel = True
        proposta.save()

    return HttpResponse(message)