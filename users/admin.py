#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.contrib import admin
#from django.contrib.auth import get_user_model
#from django.contrib.auth.admin import UserAdmin

#from .forms import PFEUserCreationForm
#from .forms import PFEUserChangeForm
from .models import PFEUser, Aluno, Professor, Parceiro, Administrador, Opcao, Alocacao

@admin.register(PFEUser)
class PFEUserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'username', 'email', 'tipo_de_usuario',) #na tabela com todos
    list_filter = ('tipo_de_usuario',)
    fieldsets = (
        (None, {'fields': ('username', 'first_name', 'last_name', 'email', 'tipo_de_usuario',)}),
        ('Personal info', {'fields': ('groups', 'user_permissions', 'cpf')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',)}),
    )
    ordering = ('first_name', 'last_name')

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('user', 'curso', 'anoPFE', 'semestrePFE')
    ordering = ('user__first_name', 'user__last_name',)

admin.site.register(Professor)
admin.site.register(Parceiro)
admin.site.register(Administrador)

class OpcaoInline(admin.TabularInline):
    model = Opcao
    extra = 5
    max_num = 5

admin.site.register(Opcao)
admin.site.register(Alocacao)
