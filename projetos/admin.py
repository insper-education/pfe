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
from .models import Projeto, Proposta, Empresa, Banca, Coorientador

# Das disciplinas
from .models import Disciplina, Cursada, Recomendada

# Das dinâmicas
from .models import Encontro, Evento

# Da coordenação
from .models import Configuracao, Aviso, Documento, Anotacao, Reembolso, Banco

# Do Insper
from .models import Entidade

# Das Organizações
from .models import Feedback, Conexao

from .models import ObjetidosDeAprendizagem, Avaliacao, Certificado

def dup_projeto(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados"""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
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

def dup_encontros(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados"""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        #obj.startDate += timedelta(days=183)
        #obj.endDate += timedelta(days=183)
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)
dup_encontros.short_description = "Duplicar Entrada(s)"

def dup_encontros_4x(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados 4 X"""
    for obj in queryset:
        for _ in range(4):
            from_id = obj.id
            obj.id = None
            obj.save()
            message = "duplicando de {} para {}".format(from_id, obj.id)
            modeladmin.log_addition(request=request, object=obj, message=message)
dup_encontros_4x.short_description = "Duplicar Entrada(s) 4 X"

def dup_encontros_8x(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados 8 X"""
    for obj in queryset:
        for _ in range(8):
            from_id = obj.id
            obj.id = None
            obj.save()
            message = "duplicando de {} para {}".format(from_id, obj.id)
            modeladmin.log_addition(request=request, object=obj, message=message)
dup_encontros_8x.short_description = "Duplicar Entrada(s) 8 X"

class FechadoFilter(SimpleListFilter):
    """Para filtrar projetos fechados."""
    title = 'Projetos Fechados'
    parameter_name = ''

    def lookups(self, request, model_admin):
        return [
            ('fechados', 'Fechados'),
            ('not_fechados', 'Não Fechados'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'fechados':
            return queryset.distinct().filter(alocacao__isnull=False)
        if self.value():
            return queryset.distinct().filter(alocacao__isnull=True)

class EventoFilter(SimpleListFilter):
    """Para filtrar eventos por semestre."""
    title = 'Publico/Semestre'
    parameter_name = ''

    def lookups(self, request, model_admin):
        opcoes = [
            ('academicos', 'Acadêmicos'),
            ('coordenacao', 'Coordenação'),
        ]
        for ano in range(2018, Configuracao.objects.all().first().ano+1):
            for semestre in range(1, 3):
                opcoes.append(("{0}.{1}".format(ano, semestre), "{0}.{1}".format(ano, semestre)))
        return opcoes

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == 'academicos':
                return queryset.distinct().filter(tipo_de_evento__lt=100)
            if self.value() == 'coordenacao':
                return queryset.distinct().filter(tipo_de_evento__gte=100)
            if self.value().split('.')[1] == '1':
                return queryset.distinct().filter(startDate__year=int(self.value().split('.')[0]),
                                                  startDate__month__lte=7)
            else:
                return queryset.distinct().filter(startDate__year=int(self.value().split('.')[0]),
                                                  startDate__month__gt=7)
        return queryset.distinct().all()

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    """Exibição no sistema de administração do Django para Projeto."""
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
            'autorizado',
            'perfil_aluno1_computacao', 'perfil_aluno1_mecanica', 'perfil_aluno1_mecatronica',
            'perfil_aluno2_computacao', 'perfil_aluno2_mecanica', 'perfil_aluno2_mecatronica',
            'perfil_aluno3_computacao', 'perfil_aluno3_mecanica', 'perfil_aluno3_mecatronica',
            'perfil_aluno4_computacao', 'perfil_aluno4_mecanica', 'perfil_aluno4_mecatronica',
            'areas_de_interesse',
            'proposta',
           )
          }),
         ('Origem', {
             'fields': ('empresa',)
         }),
        )
    actions = [dup_projeto]
    search_fields = ['titulo', 'empresa__sigla',]

@admin.register(Proposta)
class PropostaAdmin(admin.ModelAdmin):
    """Exibição no sistema de administração do Django para Proposta."""
    list_display = ('titulo', 'nome', 'organizacao', 'ano', 'semestre',)
    list_filter = ('ano', 'semestre', )
    fieldsets = \
        ((None,
          {'fields':
           ('nome', 'email', 'nome_organizacao', 'website', 'endereco',
            'contatos_tecnicos', 'contatos_administrativos',
            'descricao_organizacao', 'departamento',
            'titulo', 'descricao', 'expectativas',
            'areas_de_interesse',
            'recursos', 'observacoes',
            'ano', 'semestre',
            'autorizado', 'disponivel',
            'perfil_aluno1_computacao', 'perfil_aluno1_mecanica', 'perfil_aluno1_mecatronica',
            'perfil_aluno2_computacao', 'perfil_aluno2_mecanica', 'perfil_aluno2_mecatronica',
            'perfil_aluno3_computacao', 'perfil_aluno3_mecanica', 'perfil_aluno3_mecatronica',
            'perfil_aluno4_computacao', 'perfil_aluno4_mecanica', 'perfil_aluno4_mecatronica',
           )
          }),
         ('Origem', {
             'fields': ('organizacao',)
         }),
        )
    actions = [dup_projeto]
    search_fields = ['titulo', 'organizacao__sigla',]

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('sigla', 'nome_empresa', 'website')
    search_fields = ['nome_empresa',]

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
    list_display = ('momento', 'organizacao', 'autor',)
    ordering = ('-momento',)

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('tipo_de_documento', 'organizacao', 'usuario', 'projeto')

@admin.register(Banco)
class BancoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('nome', 'codigo')
    ordering = ('nome',)

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
    ordering = ('-startDate',)
    list_filter = ('projeto__orientador',)

@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""
    list_display = ('titulo', 'tipo_de_evento', 'delta', 'realizado',)
    list_filter = ('realizado', 'coordenacao', 'comite_pfe', 'todos_alunos',
                   'todos_orientadores', 'contatos_nas_organizacoes',)
    ordering = ('delta',)
    fieldsets = \
        ((None,
          {'fields':
           ('titulo', 'tipo_de_evento', 'delta', 'mensagem', 'realizado',)
          }),
         ('Interesse', {
             'fields': ('coordenacao', 'comite_pfe', 'todos_alunos',
                        'todos_orientadores', 'contatos_nas_organizacoes',)
         }),
        )

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """Todos os eventos do PFE com suas datas."""
    list_display = ('get_title', 'startDate', 'endDate', 'location', )
    actions = [dup_event, dup_event_183]
    list_filter = (EventoFilter,)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Para ser preenchido com feedbacks das empresas."""
    list_display = ('data', 'nome', 'email', 'empresa', )

@admin.register(Conexao)
class ConexaoAdmin(admin.ModelAdmin):
    """Conexão entre parceiro e organização."""
    list_display = ('parceiro', 'projeto',
                    'gestor_responsavel', 'mentor_tecnico', 'recursos_humanos')

@admin.register(Coorientador)
class CoorientadorAdmin(admin.ModelAdmin):
    """Conexão entre coorientador e projeto."""
    list_display = ('usuario', 'projeto')
    ordering = ('usuario__first_name', 'usuario__last_name',)

@admin.register(Encontro)
class EncontroAdmin(admin.ModelAdmin):
    """Informações dos Encontros (com os facilitadores)."""
    list_display = ('startDate', 'projeto', 'facilitador', )
    actions = [dup_encontros, dup_encontros_4x, dup_encontros_8x]

@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    """Informações das Avaliações."""
    list_display = ('projeto', 'tipo_de_avaliacao', 'avaliador', 'momento', )
    ordering = ('projeto', 'tipo_de_avaliacao', 'avaliador', 'momento', )

admin.site.register(Cursada)
admin.site.register(Recomendada)
admin.site.register(Entidade)       # Para ser preenchido com as entidades estudantis
admin.site.register(ObjetidosDeAprendizagem)
admin.site.register(Certificado)
