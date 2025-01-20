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


from administracao.models import TipoCertificado, GrupoCertificado

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"
    message = "Feito"

    #     &bull; Estudantes: <span id="t_estudantes"></span><br>
    #   &bull; Orientador: <span id="t_orientador"></span><br>
    #   &bull; Coorientação: <span id="t_coorientador"></span><br>
    #   &bull; Banca: <span id="t_banca"></span><br>
    #   &bull; Mentoria Técnica: <span id="t_mentoria_tecnica"></span><br>
    #   &bull; Mentoria Profissional: <span id="t_mentoria_profissional"></span><br>

    # tr.certificadoE td {border-color: #FF0000;}
    # tr.certificadoO td {border-color: #0000FF;}
    # tr.certificadoC td {border-color: #00FF00;}
    # tr.certificadoB td {border-color: #FF00FF;}
    # tr.certificadoMP td {border-color: #FFFF00;}
    # tr.certificadoMT td {border-color: #00FFFF;}

    # tipos_certificados = [
    #     ("Estudantes (Certificação Falconi, etc)", "Student (Falconi Certification, etc)", "E"),
    #     ("Orientadores", "Advisor", "O"),
    #     ("Coorientadores", "Co-advisor", "C"),
    #     ("Bancas", "Examination Boards", "B"),
    #     ("Mentorias Profissionais (antiga Mentorial Falconi)", "Professional Mentoring (former Falconi Mentoring)", "MP"),
    #     ("Mentorias Técnicas", "Technical Mentoring", "MT"),
    # ]
    
    tipos_c = [
        ("Estudantes (Certificação Falconi, etc)", "Student (Falconi Certification, etc)", "E", "FF0000"),
        ("Orientadores", "Advisor", "O", "0000FF"),
        ("Coorientadores", "Co-advisor", "C", "00FF00"),
        ("Bancas", "Examination Boards", "B", "FF00FF"),
        ("Mentorias Profissionais (antiga Mentorial Falconi)", "Professional Mentoring (former Falconi Mentoring)", "MP", "FFFF00"),
        ("Mentorias Técnicas", "Technical Mentoring", "MT", "00FFFF"),
    ]

    for tipo in tipos_c:
        if tipo:
            novo,_ = GrupoCertificado.objects.get_or_create(sigla=tipo[2])
            novo.nome = tipo[0]
            novo.nome_en = tipo[1]
            novo.sigla = tipo[2]
            novo.cor = tipo[3]
            novo.save()

    tipos = TipoCertificado.objects.all()
    for tipo in tipos:
        if tipo.grupo_cert == "E":
            tipo.grupo_certificado = GrupoCertificado.objects.get(sigla="E")
        elif tipo.grupo_cert == "O":
            tipo.grupo_certificado = GrupoCertificado.objects.get(sigla="O")
        elif tipo.grupo_cert == "C":
            tipo.grupo_certificado = GrupoCertificado.objects.get(sigla="C")
        elif tipo.grupo_cert == "B":
            tipo.grupo_certificado = GrupoCertificado.objects.get(sigla="B")
        elif tipo.grupo_cert == "MP":
            tipo.grupo_certificado = GrupoCertificado.objects.get(sigla="MP")
        elif tipo.grupo_cert == "MT":
            tipo.grupo_certificado = GrupoCertificado.objects.get(sigla="MT")    
        tipo.save()

    return HttpResponse(message)

