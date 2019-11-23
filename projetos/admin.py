#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Novembro de 2019
"""

from django.contrib import admin
import django.contrib.admin.options as admin_opt

# Dos projetos
from .models import Projeto, Empresa, Banca, Disciplina, Cursada, Recomendada

# Das dinâmicas
from .models import Encontro, Evento

# Da coordenação
from .models import Configuracao, Aviso, Documento, Anotacao, Reembolso, Banco

# Do Insper
from .models import Entidade

def dup_event(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados"""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        if isinstance(obj, Projeto):
            if Configuracao.objects.all().first().semestre == 1:
                obj.semestre = 2
                obj.ano = Configuracao.objects.all().first().ano
            else:
                obj.semestre = 1
                obj.ano = Configuracao.objects.all().first().ano + 1
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)
dup_event.short_description = "Duplicar Entrada(s)"

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('titulo', 'empresa', 'ano', 'semestre')
    fieldsets = (
        (None, {
            'fields': ('titulo', 'titulo_final', 'descricao', 'expectativas', 'areas', 'recursos',
            'departamento',
            'anexo', 'imagem',
            'avancado', 'ano', 'semestre', 'disponivel',
            'orientador',
            'perfil_aluno1_computacao', 'perfil_aluno1_mecanica', 'perfil_aluno1_mecatronica',
            'perfil_aluno2_computacao', 'perfil_aluno2_mecanica', 'perfil_aluno2_mecatronica',
            'perfil_aluno3_computacao', 'perfil_aluno3_mecanica', 'perfil_aluno3_mecatronica',
            'perfil_aluno4_computacao', 'perfil_aluno4_mecanica', 'perfil_aluno4_mecatronica',
            'areas_de_interesse',
             )
        }),
        ('Origem', {
            'fields': ('empresa',)
        }),
    )
    actions = [dup_event]

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('sigla', 'nome_empresa',)

@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('ano', 'semestre',)

@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('nome',)

@admin.register(Anotacao)
class AnotacaoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('data', 'organizacao', 'autor',)

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('tipo_de_documento', 'organizacao', 'usuario', 'projeto')

@admin.register(Banco)
class BancoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('nome', 'codigo')

@admin.register(Reembolso)
class ReembolsoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('usuario', 'data', 'valor')

@admin.register(Banca)
class BancaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('projeto', 'get_orientador', 'get_organizacao', 'startDate')
    def get_orientador(self, obj):
        """Retorna o orientador do projeto da Banca."""
        return obj.projeto.orientador
    get_orientador.short_description = 'Orientador'
    get_orientador.admin_order_field = 'projeto__orientador'
    def get_organizacao(self, obj):
        """Retorna a organização parceira do projeto da Banca."""
        return obj.projeto.empresa
    get_organizacao.short_description = 'Organização'
    get_organizacao.admin_order_field = 'projeto__empresa'

@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('titulo', 'delta',)

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """Todos os eventos do PFE com suas datas."""
    list_display = ('name', 'startDate', 'endDate', 'location', )
    actions = [dup_event]

admin.site.register(Cursada)
admin.site.register(Recomendada)
admin.site.register(Encontro)       # Informações das Encontros (com os facilitadores)
admin.site.register(Entidade)       # Para ser preenchido com as entidades estudantis
