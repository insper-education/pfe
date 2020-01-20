#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Novembro de 2019
"""

from datetime import timedelta

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
import django.contrib.admin.options as admin_opt

# Dos projetos
from .models import Projeto, Empresa, Banca, Disciplina, Cursada, Recomendada

# Das dinâmicas
from .models import Encontro, Evento

# Da coordenação
from .models import Configuracao, Aviso, Documento, Anotacao, Reembolso, Banco

# Do Insper
from .models import Entidade

# Das Organizações
from .models import Feedback, Conexao

def dup_projeto(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados"""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        #if isinstance(obj, Projeto):
        if Configuracao.objects.all().first().semestre == 1:
            obj.semestre = 2
            obj.ano = Configuracao.objects.all().first().ano
        else:
            obj.semestre = 1
            obj.ano = Configuracao.objects.all().first().ano + 1
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)
dup_projeto.short_description = "Duplicar Entrada(s)"

def dup_event(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados"""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)
dup_event.short_description = "Duplicar Entrada(s)"

def dup_event_183(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados"""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        obj.startDate += timedelta(days=183)
        obj.endDate += timedelta(days=183)
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)
dup_event_183.short_description = "Duplicar Entrada(s) adicionando 183 dias"

class FechadoFilter(SimpleListFilter):
    """Para filtrar projetos fechados."""
    title = 'Projetos Fechados' # a label for our filter
    parameter_name = '' # you can put anything here

    def lookups(self, request, model_admin):
        # This is where you create filter options; we have two:
        return [
            ('fechados', 'Fechados'),
            ('not_fechados', 'Não Fechados'),
        ]

    def queryset(self, request, queryset):
        # This is where you process parameters selected by use via filter options:
        if self.value() == 'fechados':
            # Get websites that have at least one page.
            #return queryset.distinct().filter(pages__isnull=False)
            return queryset.distinct().filter(alocacao__isnull=False)
        if self.value():
            # Get websites that don't have any pages.
            #return queryset.distinct().filter(pages__isnull=True)
            return queryset.distinct().filter(alocacao__isnull=True)

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('empresa', 'ano', 'semestre', 'orientador', 'get_titulo',)
    list_filter = (FechadoFilter, 'ano', 'semestre', 'avancado', 'disponivel',)
    fieldsets = \
        ((None,
          {'fields':
           ('titulo', 'titulo_final', 'descricao', 'expectativas', 'areas', 'recursos',
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
    actions = [dup_projeto]

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
    actions = [dup_event, dup_event_183]

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Para ser preenchido com feedbacks das empresas."""
    list_display = ('data', 'nome', 'email', 'empresa', )

@admin.register(Conexao)
class FeedbackAdmin(admin.ModelAdmin):
    """Conexão entre parceiro e organização."""
    list_display = ('usuario', 'projeto')

admin.site.register(Cursada)
admin.site.register(Recomendada)
admin.site.register(Encontro)       # Informações das Encontros (com os facilitadores)
admin.site.register(Entidade)       # Para ser preenchido com as entidades estudantis
