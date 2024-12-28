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


from administracao.models import TipoEvento
from projetos.tipos import TIPO_EVENTO
from projetos.models import Evento, Aviso
from academica.models import Composicao

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"
    message = "Feito"

    # Criar os tipos de eventos
    for tipo in TIPO_EVENTO:
        if TipoEvento.objects.filter(tmpID=tipo[0]).exists():
            message += f"<br>{tipo[0]} - {tipo[1]} - Já existe"
        else:
            cor = tipo[2].replace("#", "")
            TipoEvento.objects.create(tmpID=tipo[0], nome=tipo[1], cor=cor)
            message += f"<br>{tipo[0]} - {tipo[1]} - Criado"


    # Criar as composições
    for composicao in Composicao.objects.all():
        if composicao.evento is not None:
            if TipoEvento.objects.filter(tmpID=composicao.evento).exists():
                tipo_evento = TipoEvento.objects.get(tmpID=composicao.evento)
                composicao.tipo_evento = tipo_evento
                composicao.save()
                message += f"<br>{composicao.id} - {composicao.evento} - {tipo_evento.nome} - Atualizado"
            else:
                message += f"<br>{composicao.id} - {composicao.evento} - Não encontrado"
    
    # Criar os eventos
    for evento in Evento.objects.all():
        if evento.tipo_de_evento is not None:
            if TipoEvento.objects.filter(tmpID=evento.tipo_de_evento).exists():
                tipo_evento = TipoEvento.objects.get(tmpID=evento.tipo_de_evento)
                evento.tipo_evento = tipo_evento
                evento.save()
                message += f"<br>{evento.id} - {evento.tipo_de_evento} - {tipo_evento.nome} - Atualizado"
            else:
                message += f"<br>{evento.id} - {evento.tipo_de_evento} - Não encontrado"

    # Criar os avisos
    for aviso in Aviso.objects.all():
        if aviso.tipo_de_evento is not None:
            if TipoEvento.objects.filter(tmpID=aviso.tipo_de_evento).exists():
                tipo_evento = TipoEvento.objects.get(tmpID=aviso.tipo_de_evento)
                aviso.tipo_evento = tipo_evento
                aviso.save()
                message += f"<br>{aviso.id} - {aviso.tipo_de_evento} - {tipo_evento.nome} - Atualizado"
            else:
                message += f"<br>{aviso.id} - {aviso.tipo_de_evento} - Não encontrado"
    
    return HttpResponse(message)