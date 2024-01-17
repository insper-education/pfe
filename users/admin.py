#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import string
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from .models import PFEUser, Aluno, Professor, Parceiro, Administrador
from .models import Opcao, OpcaoTemporaria, Alocacao   # Mover para outra área


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
    """Usuário geral para todos do PFE."""
    list_display = ("first_name", "last_name", "username", "email", "genero", "tipo_de_usuario",)
    list_filter = ("tipo_de_usuario", "coordenacao", FirstLetterFilter)
    fieldsets = (
        (None, {"fields": ("username", "first_name", "last_name", "email", "tipo_de_usuario",)}),
        ("Personal info",
         {"fields": ("groups", "user_permissions", "telefone", "celular", "instant_messaging",
                     "linkedin", "membro_comite", "genero", "tipo_lingua", "coordenacao", "observacoes")}),
        ("Permissions",
         {"fields": ("is_active", "is_staff", "is_superuser",)}),
    )
    ordering = ("first_name", "last_name")
    search_fields = ["first_name", "last_name", ]


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    """Definição de aluno do PFE."""
    list_display = ("user", "curso2", "anoPFE", "semestrePFE")
    ordering = ("user__first_name", "user__last_name", )
    list_filter = ("curso2", FirstLetterFilter, )
    search_fields = ["user__first_name", "user__last_name", ]
    fieldsets = \
        ((None,
          {"fields":
           ("user",)
          }),
         ("Pessoais", {
             "fields": ("matricula", "curso2", 
                        #"opcoes", 
                        "email_pessoal", "anoPFE", 
                        "semestrePFE", "trancado", "cr", "pre_alocacao", 
                        "trabalhou", "social", "entidade", "familia", "externo",)
         }),
        )


@admin.register(Alocacao)
class AlocacaoAdmin(admin.ModelAdmin):
    """Definição de Alocacao do PFE."""
    list_display = ("aluno", "projeto",)
    ordering = ("-projeto__ano", "-projeto__semestre",)
    search_fields = ["aluno__user__first_name", "aluno__user__last_name", "projeto__titulo", "projeto__titulo_final", ]
    list_filter = ("projeto__ano", "projeto__semestre", )


@admin.register(Parceiro)
class ParceiroAdmin(admin.ModelAdmin):
    """Definição de Parceiro do PFE."""
    list_display = ("get_full_name", "get_sigla", "email")
    ordering = ("user__first_name", "user__last_name")
    list_filter = (FirstLetterFilter, )
    search_fields = ["user__first_name", "user__last_name", ]

    def get_full_name(self, obj):
        """Retorna o nome completo do usuário"""
        return obj.user.first_name+' '+obj.user.last_name
    get_full_name.short_description = "Nome Completo"
    get_full_name.admin_order_field = "user__first_name"

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
    get_full_name.short_description = "e-mail"


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    """Definição de Professor do PFE."""
    list_display = ("user", "lattes")
    ordering = ("user__first_name", "user__last_name", )
    list_filter = (FirstLetterFilter, )
    search_fields = ["user__first_name", "user__last_name", ]


admin.site.register(Administrador)


@admin.register(Opcao)
class OpcaoAdmin(admin.ModelAdmin):
    """Definição de Opções do PFE."""
    list_display = ("aluno", "proposta", "prioridade")
    ordering = ("aluno", )
    search_fields = ["aluno__user__first_name", "aluno__user__last_name", ]


@admin.register(OpcaoTemporaria)
class OpcaoTemporariaAdmin(admin.ModelAdmin):
    """Definição de Opções Temporárias do PFE."""
    list_display = ("aluno", "proposta", "prioridade")
    ordering = ("aluno", )
    search_fields = ["aluno__user__first_name", "aluno__user__last_name", ]


class OpcaoInline(admin.TabularInline):
    """.Não me lembro onde uso isso, provavel código morto."""
    model = Opcao
    extra = 5
    max_num = 5
