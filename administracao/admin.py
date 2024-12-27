#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Novembro de 2019
"""

from django.contrib import admin

from .models import Carta
from .models import TipoCertificado

@admin.register(Carta)
class CartaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("template",)
    ordering = ("template",)
    search_fields = ["template",]

admin.site.register(TipoCertificado)
