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
    """Página principal do sistema do Projeto Final de Engenharia."""
    # num_visits = request.session.get('num_visits', 0) # Visitas a página.
    # request.session['num_visits'] = num_visits + 1
    return render(request, "index.html")

@login_required
def index(request):
    """Página principal do sistema do Projeto Final de Engenharia."""
    return render(request, "index2.html")

def manutencao(request):
    """Página de Manutenção do Projeto Final de Engenharia."""
    return render(request, "manutencao.html")

def custom_400(request, exception):
    mensagem = "<h1>Bad Request (400)</h1>"
    if (exception):
        mensagem += str(exception) + "<br>"
    mensagem += "Em caso de dúvida " + settings.CONTATO
    #t = loader.get_template("400.html")
    #t.render(Context({"exception_value": value,})
    return HttpResponse(mensagem)

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"

    return HttpResponse(message)