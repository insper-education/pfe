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


from projetos.models import TipoRetorno, Anotacao

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"
    message = "Feito"

    for tipo in Anotacao.TIPO_DE_RETORNO:
        t,_ = TipoRetorno.objects.get_or_create(tmp_id=tipo[0], nome=tipo[1])

        if tipo[2] == "Prospecção":
            t.grupo_de_retorno = 1
        elif tipo[2] == "Retorno":
            t.grupo_de_retorno = 2
        elif tipo[2] == "Contratação":
            t.grupo_de_retorno = 3
        elif tipo[2] == "Relatório":
            t.grupo_de_retorno = 4


        if tipo[0]==254:
            t.nome = "Falta de retorno"
            t.grupo_de_retorno = 5
            t.cor = "999999"
        elif tipo[0]==6:
            t.nome = "Contrato(s) assinado(s)"
        elif tipo[0]==12:
            t.nome = "Contrato em análise jurídica (empresa)"
        elif tipo[0]==13:
            t.nome = "Empresa contactada para assinatura de contrato"
        
        if tipo[0]==0:
            t.cor = "ADD8E6"
        elif tipo[0]==1:
            t.cor = "FFFACD"
        elif tipo[0]==2:
            t.cor = "90EE90"
        elif tipo[0]==3:
            t.cor = "FFC0CB"
        elif tipo[0]==4:
            t.cor = "FFFF00"
        elif tipo[0]==5:
            t.cor = "E289DF"
        elif tipo[0]==6:
            t.cor = "7FFFD4"
        elif tipo[0]==7:
            t.cor = "FFFFE0"
        elif tipo[0]==10:
            t.cor = "11FF11"
        elif tipo[0]==11:
            t.cor = "FF1111"
        elif tipo[0]==12:
            t.cor = "FFD580"
        elif tipo[0]==13:
            t.cor = "FFDAB9"

        t.save()

    novos = [
        (14, "Contrato em fase de assinaturas (Insper)", 3),
        (15, "Contrato em fase de assinaturas (empresa)", 3),
        (16, "Contrato em análise jurídica (Insper)", 3),
    ]

    for tipo in novos:
        t,_ = TipoRetorno.objects.get_or_create(tmp_id=tipo[0], nome=tipo[1])
        t.grupo_de_retorno = tipo[2]

        if tipo[0] == 14:
            t.cor = "FFD700"  # Gold
        elif tipo[0] == 15:
            t.cor = "FF8C00"  # Dark Orange
        elif tipo[0] == 16:
            t.cor = "FFA07A"  # Light Salmon

        t.save()

    for a in Anotacao.objects.all():
        a.tipo_retorno = TipoRetorno.objects.get(tmp_id=a.tipo_de_retorno)
        a.save()

    return HttpResponse(message)

