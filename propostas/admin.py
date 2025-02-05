#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 5 de Fevereiro de 2025
"""

from django.contrib import admin

from .models import *

@admin.register(PerguntasRespostas)
class PerguntasRespostasAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("proposta", "pergunta", "resposta", "data_pergunta", "data_resposta", "quem_perguntou", "quem_respondeu")