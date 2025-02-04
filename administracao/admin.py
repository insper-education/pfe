#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Novembro de 2019
"""

from django.contrib import admin

from .models import Carta
from .models import TipoCertificado, TipoEvento, GrupoCertificado, Despesa

@admin.register(Carta)
class CartaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("template", "sigla")
    ordering = ("template",)
    search_fields = ["template", "texto"]


@admin.register(GrupoCertificado)
class GrupoCertificadoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("nome", "sigla", "cor")
    ordering = ("nome",)
    search_fields = ["nome", "sigla"]


@admin.register(TipoCertificado)
class TipoCertificadoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("titulo", "sigla", "grupo_certificado")
    ordering = ("titulo",)
    search_fields = ["titulo", "sigla"]


@admin.register(TipoEvento)
class TipoEventoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ("nome", "sigla", "cor")
    ordering = ("nome",)
    search_fields = ["nome", "sigla"]

@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""


    # projeto = models.ForeignKey("projetos.Projeto", on_delete=models.CASCADE,
    #                             help_text="Projeto")
    
    # data = models.DateField("Data", null=True, blank=True,
    #                         help_text="Data da despesa")
    
    # descricao = models.CharField("Descrição", max_length=256, null=True, blank=True,
    #                             help_text="Descrição da despesa")
    
    # valor_r = models.DecimalField("Valor", max_digits=12, decimal_places=2, null=True, blank=True,
    #                             help_text="Valor da despesa em reais")
    
    # valor_d = models.DecimalField("Valor", max_digits=12, decimal_places=2, null=True, blank=True,
    #                             help_text="Valor da despessa em dólares")
    

    list_display = ("projeto", "data", "descricao", "valor_r", "valor_d")
    ordering = ("projeto",)
    search_fields = ["projeto", "descricao"]
    list_filter = ["data"]


