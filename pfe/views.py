#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2023
"""

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from administracao.models import Carta

# Get an instance of a logger
logger = logging.getLogger("django")

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
        info = get_object_or_404(Carta, template="Informação")
        return render(request, "info.html", {"info": info})

def info(request):
    """Página com informações."""
    info = get_object_or_404(Carta, template="Informação")
    return render(request, "info.html", {"info": info})

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

from projetos.models import Banca
from academica.models import Composicao


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"
    message = "Feito"

    bancas = Banca.objects.all()
    for banca in bancas:
        if banca.tipo_de_banca == 0:  # Banca Final
            composicao = Composicao.objects.filter(exame__sigla="BF", data_inicial__lte=banca.startDate).order_by("-data_inicial").first()
        elif banca.tipo_de_banca == 1:  # Banca Intermediária
            composicao = Composicao.objects.filter(exame__sigla="BI", data_inicial__lte=banca.startDate).order_by("-data_inicial").first()
        elif banca.tipo_de_banca == 2:  # Banca Falconi
            composicao = Composicao.objects.filter(exame__sigla="F", data_inicial__lte=banca.startDate).order_by("-data_inicial").first()
        elif banca.tipo_de_banca == 3: # Banca Probation
            composicao = Composicao.objects.filter(exame__sigla="P", data_inicial__lte=banca.startDate).order_by("-data_inicial").first()
        else:
            return HttpResponse("Tipo de Banca não reconhecido")

        banca.composicao = composicao
        banca.save()

    # Só para testar se envia mensagem
    logger.warning(f"SOMENTE UM TESTE DE WARNING")

    return HttpResponse(message)