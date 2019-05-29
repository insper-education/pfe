from django.contrib import admin

from .models import Projeto, Empresa, Configuracao

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'empresa', 'ano', 'semestre')
    fieldsets = (
        (None, {
            'fields': ('titulo', 'descricao', 'expectativas', 'areas', 'recursos', 'imagem', 'ano', 'semestre', 'disponivel')
        }),
        ('Origem', {
            'fields': ('empresa',)
        }),
    )

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome_empresa')

@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ('ano', 'semestre')
