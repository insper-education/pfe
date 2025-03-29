#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import datetime
import logging

from django.shortcuts import render

from projetos.models import Projeto, Evento, FeedbackEstudante


# Get an instance of a logger
logger = logging.getLogger("django")


def estudante_feedback_geral(request, usuario):
    """Para Feedback finais dos Estudantes."""
    mensagem = ""
    
    if usuario.tipo_de_usuario in (2, 4): # Caso professor ou administrador
        mensagem = "Você está acessando como administrador!<br>Esse formulário fica disponível para os estudantes após as bancas finais."
        projeto = None

    elif usuario.tipo_de_usuario == 1: # Estudante
        hoje = datetime.date.today()
        projeto = Projeto.objects.filter(alocacao__aluno=usuario.aluno).last()
        evento_banca_final = Evento.get_evento(nome="Bancas Finais", ano=projeto.ano, semestre=projeto.semestre)
        if not evento_banca_final or (evento_banca_final and hoje <= evento_banca_final.endDate):
            mensagem_erro = {
                "pt": "Fora do período de feedback do Capstone!",
                "en": "It is not the Capstone feedback period!",
            }
            context = {"mensagem_erro": mensagem_erro,}
            return render(request, "generic_ml.html", context=context)

    if request.method == "POST":
        feedback = FeedbackEstudante()
        feedback.estudante = usuario.aluno
        feedback.projeto = projeto

        recomendaria = request.POST.get("recomendaria", None)
        if recomendaria:
            feedback.recomendaria = int(recomendaria[len("option"):])
            
        primeira_opcao = request.POST.get("primeira_opcao", None)
        if primeira_opcao:
            feedback.primeira_opcao = primeira_opcao[len("option"):] == "S"

        proposta = request.POST.get("proposta", None)
        if proposta:
            feedback.proposta = int(proposta[len("option"):])

        trabalhando = request.POST.get("trabalhando", None)
        if trabalhando:
            feedback.trabalhando = int(trabalhando[len("option"):])

        feedback.outros = request.POST.get("outros", "")

        feedback.save()

        context = {
            "mensagem": {"pt": "Feedback recebido, obrigado!", "en": "Feedback received, thank you!",},
        }
        return render(request, "generic_ml.html", context=context)

    context = {
        "titulo": {"pt": "Formulário de Feedback dos Estudantes", "en": "Student Feedback Form"},
        "usuario": usuario,
        "projeto": projeto,
        "organizacao": projeto.proposta.organizacao if projeto else "[Organização/Organization]",
        "mensagem_aviso": {"pt": mensagem, "en": mensagem},
    }
    return render(request, "estudantes/estudante_feedback.html", context)
