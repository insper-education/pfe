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


from administracao.models import TipoCertificado
from projetos.tipos import TIPO_DE_CERTIFICADO
from projetos.models import Certificado

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"
    message = "Feito"

    for tipo in TIPO_DE_CERTIFICADO:
        obj, _ = TipoCertificado.objects.get_or_create(tmpID=tipo[0], titulo=tipo[1])
        
        if tipo[0] == 1:
            tipo = "_estudante_destaque"
            template = None
            grupo_cert = "E"
        elif tipo[0] == 2:
            tipo = "_equipe_destaque"
            template = None
            grupo_cert = "E"
        elif tipo[0] == 11:
            tipo = "_estudantes_destaque_falconi"
            template = None
            grupo_cert = "E"
        elif tipo[0] == 12:
            tipo = "_estudantes_excelencia_falconi"
            template = None
            grupo_cert = "E"
        if tipo[0] == 101:
            tipo = "_orientacao"
            template = get_object_or_404(Carta, template="Certificado Orientador") # 101
            grupo_cert = "O"
        elif tipo[0] == 102:
            tipo = "_coorientacao"
            template = get_object_or_404(Carta, template="Certificado Coorientador")  # (102, "Coorientação de Projeto")
            grupo_cert = "C"
        elif tipo[0] == 103:
            tipo = "_banca_intermediaria"
            template = get_object_or_404(Carta, template="Certificado Banca Intermediária")
            grupo_cert = "B"
        elif tipo[0] == 104:
            tipo = "_banca_final"
            template = get_object_or_404(Carta, template="Certificado Banca Final")
            grupo_cert = "B"
        elif tipo[0] == 105:
            tipo = "_banca_falconi"
            template = get_object_or_404(Carta, template="Certificado Banca Falconi")
            grupo_cert = "B"
        elif tipo[0] == 106:
            tipo = "_mentoria_profissional"
            template = get_object_or_404(Carta, template="Certificado Mentoria Profissional")
            grupo_cert = "MP"
        elif tipo[0] == 107:
            tipo = "_mentoria_tecnica"
            template = get_object_or_404(Carta, template="Certificado Mentoria Técnica")
            grupo_cert = "MT"
        elif tipo[0] == 108:
            tipo = "_banca_probation"
            template = get_object_or_404(Carta, template="Certificado Banca Probatória")
            grupo_cert = "B"
        else:
            tipo = ""
            template = None
            grupo_cert = ""
        
        obj.subtitulo = tipo
        obj.template = template
        obj.grupo_cert = grupo_cert

        obj.save()


    for certificado in Certificado.objects.all():   
        tipo = TipoCertificado.objects.get(tmpID=certificado.tipo_de_certificado)
        certificado.tipo_certificado = tipo
        certificado.save()

    return HttpResponse(message)