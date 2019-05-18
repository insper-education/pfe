from django.contrib import admin

from .models import Projeto, Empresa

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
