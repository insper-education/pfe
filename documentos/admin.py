#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 5 de Fevereiro de 2025
"""

from django.contrib import admin

from .models import *


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    """Tipo Documento."""
    list_display = ("nome", "sigla", "projeto", "gravar", "arquivo", "link",)
    search_fields = ["nome",]
