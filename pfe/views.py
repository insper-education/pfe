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

from projetos.models import Configuracao
from administracao.models import Estrutura, Carta

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"
    message = "Feito"
    
    configuracao = get_object_or_404(Configuracao)

    index_documentos = Estrutura.objects.get_or_create(nome="Index Documentos", sigla="IDOC")[0]
    index_documentos.descricao = "Documentos a serem mostrados no Index Documentos"
    index_documentos.json = configuracao.index_documentos
    index_documentos.save()

    niveis_objetivos = Estrutura.objects.get_or_create(nome="Níveis de Objetivos", sigla="NOBJ")[0]
    niveis_objetivos.descricao = "Níveis de Avaliação dos Objetivos de Aprendizagem"
    niveis_objetivos.json = configuracao.niveis_objetivos
    niveis_objetivos.save()

    horarios_semanais = Estrutura.objects.get_or_create(nome="Horarios Semanais", sigla="HSEM")[0]
    horarios_semanais.descricao = "Horários de Trabalho Semanais dos Estudantes"
    horarios_semanais.json = configuracao.horarios_semanais
    horarios_semanais.save()

    questoes_funcionalidade = Estrutura.objects.get_or_create(nome="Questões de Funcionalidade", sigla="QFUNC")[0]
    questoes_funcionalidade.descricao = "Questões de Funcionalidade"
    questoes_funcionalidade.json = configuracao.questoes_funcionalidade
    questoes_funcionalidade.save()

    codigo_conduta = Estrutura.objects.get_or_create(nome="Código de Conduta Individual", sigla="CCIND")[0]
    codigo_conduta.descricao = "Código de Conduta Individual"
    codigo_conduta.json = configuracao.codigo_conduta
    codigo_conduta.save()

    codigo_conduta_projeto = Estrutura.objects.get_or_create(nome="Código de Conduta do Grupo", sigla="CCGRP")[0]
    codigo_conduta_projeto.descricao = "Código de Conduta do Grupo"
    codigo_conduta_projeto.json = configuracao.codigo_conduta_projeto
    codigo_conduta_projeto.save()

    carta_informacao = Carta.objects.get_or_create(template="Mensagem Avaliação de Pares", sigla="MAP")[0]
    carta_informacao.texto = configuracao.msg_aval_pares
    carta_informacao.texto_en = "Fill out this peer feedback form for each member of your team. The messages for your group members, if used, will be compiled anonymously along with those from all other team members. Write your messages using anonymous language if you do not wish your feedback to identify you. This process aims to help someone learn, grow, or change. The focus is on helping the person improve, whether it involves a skill, an idea, knowledge, a specific practice, professional presentation, or their soft skills."
    carta_informacao.save()

    return HttpResponse(message)

