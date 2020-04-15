#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import string
from django.contrib import admin
#from django.contrib.auth import get_user_model
#from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import SimpleListFilter

#from .forms import PFEUserCreationForm
#from .forms import PFEUserChangeForm
from .models import PFEUser, Aluno, Professor, Parceiro, Administrador

from .models import Opcao, Alocacao, Areas   # Mover para outra área

class FirstLetterFilter(SimpleListFilter):
    """Filtro para separar pela primeira letra do nome."""
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Primeira Letra'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'letter'
    letters = list(string.ascii_uppercase)

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        lookups = []
        for letter in self.letters:
            count = qs.filter(user__first_name__istartswith=letter).count()
            if count:
                lookups.append((letter, '{} ({})'.format(letter, count)))
        return lookups

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        filter_val = self.value()
        if filter_val in self.letters:
            return queryset.filter(user__first_name__istartswith=self.value())

@admin.register(PFEUser)
class PFEUserAdmin(admin.ModelAdmin):
    """Usuário geral para todos do PFE."""
    list_display = ('first_name', 'last_name', 'username', 'email', 'genero', 'tipo_de_usuario',)
    list_filter = ('tipo_de_usuario',)
    fieldsets = (
        (None, {'fields': ('username', 'first_name', 'last_name', 'email', 'tipo_de_usuario',)}),
        ('Personal info',
         {'fields': ('groups', 'user_permissions', 'cpf', 'membro_comite', 'genero')}),
        ('Permissions',
         {'fields': ('is_active', 'is_staff', 'is_superuser',)}),
    )
    ordering = ('first_name', 'last_name')

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    """Definição de aluno do PFE."""
    list_display = ('user', 'curso', 'anoPFE', 'semestrePFE')
    ordering = ('user__first_name', 'user__last_name',)
    list_filter = (FirstLetterFilter, )


@admin.register(Alocacao)
class AlocacaoAdmin(admin.ModelAdmin):
    """Definição de Alocacao do PFE."""
    list_display = ('aluno', 'projeto',)
    ordering = ('-projeto__ano', '-projeto__semestre',)

@admin.register(Parceiro)
class ParceiroAdmin(admin.ModelAdmin):
    """Definição de Parceiro do PFE."""
    list_display = ('get_full_name', 'get_sigla', 'email', 'telefone', 'celular', 'skype')
    ordering = ('user__first_name', 'user__last_name',)
    list_filter = (FirstLetterFilter, )

    def get_full_name(self, obj):
        """Retorna o nome completo do usuário"""
        return obj.user.first_name+" "+obj.user.last_name
    get_full_name.short_description = 'Nome Completo'
    get_full_name.admin_order_field = 'user__first_name'

    def get_sigla(self, obj):
        """Retorna a silga da organização"""
        if obj.organizacao:
            return obj.organizacao.sigla
        else:
            return "Não Definida"
    get_sigla.short_description = 'Sigla'
    get_sigla.admin_order_field = 'organizacao__sigla'

    def email(self, obj):
        """Retorna o e-mail do usuário"""
        return obj.user.email
    get_full_name.short_description = 'e-mail'

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    """Definição de Professor do PFE."""
    list_display = ('user', 'lattes')
    ordering = ('user__first_name', 'user__last_name',)
    list_filter = (FirstLetterFilter, )

admin.site.register(Administrador)

@admin.register(Opcao)
class OpcaoAdmin(admin.ModelAdmin):
    """Definição de Opções do PFE."""
    list_display = ('aluno', 'projeto', 'prioridade')
    ordering = ('aluno',)

admin.site.register(Areas)

class OpcaoInline(admin.TabularInline):
    """.Não me lembro onde uso isso, provavel código morto."""
    model = Opcao
    extra = 5
    max_num = 5
