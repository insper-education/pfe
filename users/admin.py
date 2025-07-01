#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import string
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from .models import *


class FirstLetterFilter(SimpleListFilter):
    """Filtro para separar pela primeira letra do nome."""
    # Titulo no painel de busca
    title = "Primeira Letra"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "letter"
    letters = list(string.ascii_uppercase)

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        lookups = []
        for letter in self.letters:
            if isinstance(model_admin, PFEUserAdmin):
                count = qs.filter(first_name__istartswith=letter).count()
            else:
                count = qs.filter(user__first_name__istartswith=letter).count()
            if count:
                lookups.append((letter, "{} ({})".format(letter, count)))
        return lookups

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        filter_val = self.value()
        if filter_val in self.letters:
            if "pfeuser" in str(request):  # isso não está nada bom
                return queryset.filter(first_name__istartswith=self.value())
            return queryset.filter(user__first_name__istartswith=self.value())


@admin.register(PFEUser)
class PFEUserAdmin(admin.ModelAdmin):
    """Usuário geral ."""
    list_display = ("first_name", "last_name", "username", "email", "genero", "tipo_de_usuario",)
    list_filter = ("tipo_de_usuario", FirstLetterFilter)
    ordering = ("first_name", "last_name")
    search_fields = ["first_name", "last_name", ]


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    """Definição de usuário Estudante."""
    list_display = ("get_full_name", "curso2", "ano", "semestre", "cr")
    ordering = ("user__first_name", "user__last_name", )
    list_filter = ("curso2", FirstLetterFilter, )
    search_fields = ["user__first_name", "user__last_name", ]

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = "Nome completo"
    get_full_name.admin_order_field = "user__first_name"

@admin.register(Alocacao)
class AlocacaoAdmin(admin.ModelAdmin):
    """Definição de alocacao em projeto."""
    list_display = ("aluno", "projeto",)
    ordering = ("-projeto__ano", "-projeto__semestre",)
    search_fields = ["aluno__user__first_name", "aluno__user__last_name", "projeto__titulo_final", "projeto__proposta__titulo", ]
    list_filter = ("projeto__ano", "projeto__semestre", )


@admin.register(UsuarioEstiloComunicacao)
class UsuarioEstiloComunicacaoAdmin(admin.ModelAdmin):
    """Definição de Estilo de Comunicação."""
    list_display = ("usuario", "estilo_comunicacao")
    ordering = ("usuario", )
    search_fields = ["usuario__first_name", "usuario__last_name", ]


@admin.register(Parceiro)
class ParceiroAdmin(admin.ModelAdmin):
    """Definição de Parceiro."""
    list_display = ("user", "get_sigla", "email")
    ordering = ("user__first_name", "user__last_name")
    list_filter = (FirstLetterFilter, "user__genero", )
    search_fields = ["user__first_name", "user__last_name", ]

    def get_sigla(self, obj):
        """Retorna a silga da organização"""
        if obj.organizacao:
            return obj.organizacao.sigla
        else:
            return "Não Definida"
    get_sigla.short_description = "Sigla"
    get_sigla.admin_order_field = "organizacao__sigla"

    def email(self, obj):
        """Retorna o e-mail do usuário"""
        return obj.user.email
    email.short_description = "e-mail"


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    """Definição de Professor."""
    list_display = ("user", "lattes")
    ordering = ("user__first_name", "user__last_name", )
    list_filter = (FirstLetterFilter, )
    search_fields = ["user__first_name", "user__last_name", ]


admin.site.register(Administrador)
admin.site.register(Contato)


@admin.register(Opcao)
class OpcaoAdmin(admin.ModelAdmin):
    """Definição de Opções de escolha de propostas."""
    list_display = ("aluno", "proposta", "prioridade")
    ordering = ("aluno", )
    search_fields = ["aluno__user__first_name", "aluno__user__last_name", ]


@admin.register(OpcaoTemporaria)
class OpcaoTemporariaAdmin(admin.ModelAdmin):
    """Definição de Opções Temporárias de escolha de propostas."""
    list_display = ("aluno", "proposta", "prioridade")
    ordering = ("aluno", )
    search_fields = ["aluno__user__first_name", "aluno__user__last_name", ]


class OpcaoInline(admin.TabularInline):
    """.Não me lembro onde uso isso, provavel código morto."""
    model = Opcao
    extra = 5
    max_num = 5
