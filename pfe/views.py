#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2023
"""

import json
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

from projetos.models import Configuracao, ObjetivosDeAprendizagem
from administracao.models import Estrutura, Carta

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"
    
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

    for oa in ObjetivosDeAprendizagem.objects.all():
        rubrica = {}
        rubrica["intermediaria"] = {}
        rubrica["final"] = {}

        rubrica["intermediaria"]["grupo"] = {}
        rubrica["intermediaria"]["individual"] = {}

        rubrica["final"]["grupo"] = {}
        rubrica["final"]["individual"] = {}


        rubrica["intermediaria"]["grupo"]["I"] = {}
        rubrica["intermediaria"]["grupo"]["I"]["pt"] = oa.rubrica_intermediaria_I
        rubrica["intermediaria"]["grupo"]["I"]["en"] = oa.rubrica_intermediaria_I_en

        rubrica["intermediaria"]["grupo"]["D"] = {}
        rubrica["intermediaria"]["grupo"]["D"]["pt"] = oa.rubrica_intermediaria_D
        rubrica["intermediaria"]["grupo"]["D"]["en"] = oa.rubrica_intermediaria_D_en

        rubrica["intermediaria"]["grupo"]["C"] = {}
        rubrica["intermediaria"]["grupo"]["C"]["pt"] = oa.rubrica_intermediaria_C
        rubrica["intermediaria"]["grupo"]["C"]["en"] = oa.rubrica_intermediaria_C_en

        rubrica["intermediaria"]["grupo"]["B"] = {}
        rubrica["intermediaria"]["grupo"]["B"]["pt"] = oa.rubrica_intermediaria_B
        rubrica["intermediaria"]["grupo"]["B"]["en"] = oa.rubrica_intermediaria_B_en

        rubrica["intermediaria"]["grupo"]["A"] = {}
        rubrica["intermediaria"]["grupo"]["A"]["pt"] = oa.rubrica_intermediaria_A
        rubrica["intermediaria"]["grupo"]["A"]["en"] = oa.rubrica_intermediaria_A_en

        
        rubrica["final"]["grupo"]["I"] = {}
        rubrica["final"]["grupo"]["I"]["pt"] = oa.rubrica_final_I
        rubrica["final"]["grupo"]["I"]["en"] = oa.rubrica_final_I_en

        rubrica["final"]["grupo"]["D"] = {}
        rubrica["final"]["grupo"]["D"]["pt"] = oa.rubrica_final_D
        rubrica["final"]["grupo"]["D"]["en"] = oa.rubrica_final_D_en

        rubrica["final"]["grupo"]["C"] = {}
        rubrica["final"]["grupo"]["C"]["pt"] = oa.rubrica_final_C
        rubrica["final"]["grupo"]["C"]["en"] = oa.rubrica_final_C_en

        rubrica["final"]["grupo"]["B"] = {}
        rubrica["final"]["grupo"]["B"]["pt"] = oa.rubrica_final_B
        rubrica["final"]["grupo"]["B"]["en"] = oa.rubrica_final_B_en

        rubrica["final"]["grupo"]["A"] = {}
        rubrica["final"]["grupo"]["A"]["pt"] = oa.rubrica_final_A
        rubrica["final"]["grupo"]["A"]["en"] = oa.rubrica_final_A_en

        rubrica["intermediaria"]["individual"]["I"] = {}
        rubrica["intermediaria"]["individual"]["I"]["pt"] = oa.rubrica_intermediaria_individual_I
        rubrica["intermediaria"]["individual"]["I"]["en"] = oa.rubrica_intermediaria_individual_I_en

        rubrica["intermediaria"]["individual"]["D"] = {}
        rubrica["intermediaria"]["individual"]["D"]["pt"] = oa.rubrica_intermediaria_individual_D
        rubrica["intermediaria"]["individual"]["D"]["en"] = oa.rubrica_intermediaria_individual_D_en

        rubrica["intermediaria"]["individual"]["C"] = {}
        rubrica["intermediaria"]["individual"]["C"]["pt"] = oa.rubrica_intermediaria_individual_C
        rubrica["intermediaria"]["individual"]["C"]["en"] = oa.rubrica_intermediaria_individual_C_en

        rubrica["intermediaria"]["individual"]["B"] = {}
        rubrica["intermediaria"]["individual"]["B"]["pt"] = oa.rubrica_intermediaria_individual_B
        rubrica["intermediaria"]["individual"]["B"]["en"] = oa.rubrica_intermediaria_individual_B_en

        rubrica["intermediaria"]["individual"]["A"] = {}
        rubrica["intermediaria"]["individual"]["A"]["pt"] = oa.rubrica_intermediaria_individual_A
        rubrica["intermediaria"]["individual"]["A"]["en"] = oa.rubrica_intermediaria_individual_A_en

        
        rubrica["final"]["individual"]["I"] = {}
        rubrica["final"]["individual"]["I"]["pt"] = oa.rubrica_final_individual_I
        rubrica["final"]["individual"]["I"]["en"] = oa.rubrica_final_individual_I_en

        rubrica["final"]["individual"]["D"] = {}
        rubrica["final"]["individual"]["D"]["pt"] = oa.rubrica_final_individual_D
        rubrica["final"]["individual"]["D"]["en"] = oa.rubrica_final_individual_D_en

        rubrica["final"]["individual"]["C"] = {}
        rubrica["final"]["individual"]["C"]["pt"] = oa.rubrica_final_individual_C
        rubrica["final"]["individual"]["C"]["en"] = oa.rubrica_final_individual_C_en

        rubrica["final"]["individual"]["B"] = {}
        rubrica["final"]["individual"]["B"]["pt"] = oa.rubrica_final_individual_B
        rubrica["final"]["individual"]["B"]["en"] = oa.rubrica_final_individual_B_en

        rubrica["final"]["individual"]["A"] = {}
        rubrica["final"]["individual"]["A"]["pt"] = oa.rubrica_final_individual_A
        rubrica["final"]["individual"]["A"]["en"] = oa.rubrica_final_individual_A_en

        # Record dictionary as JSON
        oa.rubrica = json.dumps(rubrica, ensure_ascii=False)
        oa.save()

    message = "Feito"
    return HttpResponse(message)
