#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Novembro de 2019
"""

from django.contrib import admin

from .models import Carta
from .models import TipoCertificado, TipoEvento, GrupoCertificado

@admin.register(Carta)
class CartaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("template",)
    ordering = ("template",)
    search_fields = ["template", "texto"]

@admin.register(TipoCertificado)
class TipoCertificadoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("titulo", "sigla", "grupo_certificado")
    ordering = ("titulo",)
    search_fields = ["titulo", "sigla"]

admin.site.register(GrupoCertificado)

@admin.register(TipoEvento)
class TipoEventoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("nome", "sigla", "cor")
    ordering = ("nome",)
    search_fields = ["nome", "sigla"]
