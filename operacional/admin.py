#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 27 de Dezembro de 2022
"""

from django.contrib import admin
from .models import Curso

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    """Definição de Curso do PFE."""
    list_display = ("nome", "sigla", "sigla_curta", "cor", )
    ordering = ("nome", )
    search_fields = ["nome", ]

