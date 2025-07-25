#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Novembro de 2019
"""

from datetime import timedelta

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
import django.contrib.admin.options as admin_opt

from .models import *


def dup_projeto(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        if Configuracao.objects.get().semestre == 1:
            obj.semestre = 2
            obj.ano = Configuracao.objects.get().ano
        else:
            obj.semestre = 1
            obj.ano = Configuracao.objects.get().ano + 1
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)


dup_projeto.short_description = "Duplicar Entrada(s)"


def dup_entrada(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    # Usada em Eventos e Avisos
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)

dup_entrada.short_description = "Duplicar Entrada(s)"


def dup_event_182(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        obj.startDate += timedelta(days=182)
        obj.endDate += timedelta(days=182)
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)


dup_event_182.short_description = "Duplicar Entrada(s) adicionando 182 dias"


def dup_encontros(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados."""
    for obj in queryset:
        from_id = obj.id
        obj.id = None
        obj.save()
        message = "duplicando de {} para {}".format(from_id, obj.id)
        modeladmin.log_addition(request=request, object=obj, message=message)


dup_encontros.short_description = "Duplicar Entrada(s)"


def dup_encontros_4x(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados 4 X."""
    for obj in queryset:
        for _ in range(4):
            from_id = obj.id
            obj.id = None
            obj.save()
            message = "duplicando de {} para {}".format(from_id, obj.id)
            modeladmin.log_addition(request=request, object=obj, message=message)


dup_encontros_4x.short_description = "Duplicar Entrada(s) 4 X"


def dup_encontros_8x(modeladmin: admin_opt.ModelAdmin, request, queryset):
    """Função abaixo permite duplicar entradas no banco de dados 8 X."""
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

    title = "Projetos Fechados"
    parameter_name = ""

    def lookups(self, request, model_admin):
        return [
            ("fechados", "Fechados"),
            ("not_fechados", "Não Fechados"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "fechados":
            return queryset.distinct().filter(alocacao__isnull=False)
        if self.value():
            return queryset.distinct().filter(alocacao__isnull=True)
        return None
    

class AnoSemestreFilter(SimpleListFilter):
    """Para filtrar projetos por ano e semestre."""

    title = "Ano/Semestre"
    parameter_name = ""

    def lookups(self, request, model_admin):
        opcoes = []
        for ano in range(2018, Configuracao.objects.get().ano+2):
            for semestre in range(1, 3):
                opcoes.append(("{0}.{1}".format(ano, semestre), "{0}.{1}".format(ano, semestre)))
        return opcoes

    def queryset(self, request, queryset):
        if self.value():
            q_aluno = queryset.distinct().filter(usuario__aluno__ano=int(self.value().split('.')[0]),
                                                 usuario__aluno__semestre=int(self.value().split('.')[1]))
            q_proposta = queryset.distinct().filter(proposta__ano=int(self.value().split('.')[0]),
                                                    proposta__semestre=int(self.value().split('.')[1]))
            
            return q_aluno | q_proposta
                                                    
        return queryset.distinct().all()


class EventoFilter(SimpleListFilter):
    """Para filtrar eventos por semestre."""

    title = "Publico/Semestre"
    parameter_name = ""

    def lookups(self, request, model_admin):
        opcoes = [
            ("academicos", "Acadêmicos"),
            ("coordenacao", "Coordenação"),
        ]
        for ano in range(2018, Configuracao.objects.get().ano+2):
            for semestre in range(1, 3):
                opcoes.append(("{0}.{1}".format(ano, semestre), "{0}.{1}".format(ano, semestre)))
        return opcoes

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == "academicos":
                return queryset.distinct().filter(tipo_evento__coodenacao=False)
            if self.value() == "coordenacao":
                return queryset.distinct().filter(tipo_evento__coodenacao=True)
            if self.value().split(".")[1] == "1":
                return queryset.distinct().filter(startDate__year=int(self.value().split('.')[0]),
                                                  startDate__month__lte=7)
            else:
                return queryset.distinct().filter(startDate__year=int(self.value().split('.')[0]),
                                                  startDate__month__gt=7)
        return queryset.distinct().all()


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    """Exibição no sistema de administração do Django para Projeto."""

    list_display = ("organizacao", "ano", "semestre", "orientador", "get_titulo",)
    list_filter = (FechadoFilter, "ano", "semestre",)
    actions = [dup_projeto]
    search_fields = ["titulo_final", "proposta__organizacao__sigla", "orientador__user__first_name" ]


@admin.register(Proposta)
class PropostaAdmin(admin.ModelAdmin):
    """Exibição no sistema de administração do Django para Proposta."""

    list_display = ("titulo", "nome", "organizacao", "ano", "semestre", )
    list_filter = ("ano", "semestre", )
    actions = [dup_projeto]
    search_fields = ["titulo", "organizacao__sigla",]


@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    """Definição da Organização no sistema de administração do Django."""

    list_display = ("sigla", "nome", "website")
    search_fields = ["nome",]


@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("ano", "semestre",)


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("nome",)
    ordering = ("nome",)
    search_fields = ["nome",]


@admin.register(Anotacao)
class AnotacaoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("momento", "organizacao", "tipo_retorno", "autor",)
    list_filter = ("tipo_retorno",)
    ordering = ("-momento",)
    search_fields = ["organizacao__nome",]


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("tipo_documento", "data", "confidencial", "organizacao", "usuario", "projeto")
    list_filter = ("data", "tipo_documento", "confidencial", "lingua_do_documento", )
    search_fields = ["projeto__titulo_final", "projeto__proposta__titulo",
                     "usuario__username", "projeto__proposta__organizacao__sigla",]
    actions = [dup_entrada]

@admin.register(Banco)
class BancoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("nome", "codigo")
    ordering = ("nome",)


@admin.register(Reembolso)
class ReembolsoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("usuario", "data", "valor")


@admin.register(Banca)
class BancaAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("composicao", "projeto", "get_orientador", "get_organizacao", "startDate", "slug",)
    list_filter = ("composicao__exame", "projeto__ano", "projeto__semestre",)
    search_fields = ["projeto__titulo_final", "projeto__proposta__organizacao__sigla", 
                     "projeto__orientador__user__first_name", "projeto__orientador__user__last_name",
                     "membro1__first_name", "membro1__last_name",
                     "membro2__first_name", "membro2__last_name",
                     "membro3__first_name", "membro3__last_name",]

    def get_orientador(self, obj):
        """Retorna o orientador do projeto da Banca."""
        if obj.projeto and obj.projeto.orientador:
            return obj.projeto.orientador
        return None
    get_orientador.short_description = "Orientador"
    get_orientador.admin_order_field = "projeto__orientador"

    def get_organizacao(self, obj):
        """Retorna a organização parceira do projeto da Banca."""
        if obj.projeto and obj.projeto.organizacao:
            return obj.projeto.organizacao
        return None
    get_organizacao.short_description = "Organização"
    get_organizacao.admin_order_field = "projeto__organizacao"
    ordering = ("-startDate",)


@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    """Definição do que aparece no sistema de administração do Django."""

    list_display = ("titulo", "tipo_evento", "delta",) # "realizado", "data_realizado",)
    list_filter = ("coordenacao", "comite", "todos_alunos",  # "realizado",
                   "todos_orientadores", "contatos_nas_organizacoes",)
    search_fields = ["titulo", "mensagem",]
    ordering = ("delta",)
    actions = [dup_entrada]


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """Todos os eventos com suas datas."""

    list_display = ("get_title", "startDate", "endDate", "location", "atividade", "observacao")
    actions = [dup_entrada, dup_event_182]
    list_filter = (EventoFilter, "tipo_evento")
    ordering = ("-startDate",)
    search_fields = ["atividade", "location", "observacao",]

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Para ser preenchido com feedbacks das organizacoes."""

    list_display = ("data", "nome", "email", "empresa", )


@admin.register(FeedbackEstudante)
class FeedbackAdmin(admin.ModelAdmin):
    """Para ser preenchido com feedbacks dos estudantes."""

    list_display = ("momento", "estudante", "projeto", )

@admin.register(Conexao)
class ConexaoAdmin(admin.ModelAdmin):
    """Conexão entre parceiro e organização."""

    list_display = ("parceiro", "projeto",
                    "gestor_responsavel", "mentor_tecnico", "recursos_humanos", "colaboracao")
    search_fields = ["parceiro__user__first_name", "parceiro__user__last_name",
                     "projeto__titulo_final", "projeto__proposta__titulo", "projeto__titulo_final",]


@admin.register(Coorientador)
class CoorientadorAdmin(admin.ModelAdmin):
    """Conexão entre coorientador e projeto."""

    list_display = ("usuario", "projeto")
    ordering = ("usuario__first_name", "usuario__last_name",)
    search_fields = ["usuario__first_name", "usuario__last_name",]


@admin.register(Encontro)
class EncontroAdmin(admin.ModelAdmin):
    """Informações dos Encontros (com os facilitadores)."""

    list_display = ("startDate", "hora_fim", "projeto", "facilitador", )
    actions = [dup_encontros, dup_encontros_4x, dup_encontros_8x]
    search_fields = ["projeto__titulo_final", "projeto__proposta__titulo","facilitador__username",]


@admin.register(Avaliacao2)
class Avaliacao2Admin(admin.ModelAdmin):
    """Informações das Avaliações2."""

    list_display = ("momento", "nota", "peso", "objetivo",
                    "exame", "avaliador", "projeto", "alocacao")
    ordering = ("-momento",)
    list_filter = ("exame", "objetivo", "projeto__ano", "projeto__semestre")
    search_fields = ["projeto__titulo_final", "projeto__proposta__titulo",
                     "alocacao__aluno__user__username", "projeto__proposta__organizacao__sigla"]


@admin.register(Avaliacao_Velha)
class Avaliacao_VelhaAdmin(admin.ModelAdmin):
    """Informações das Avaliações Velhas."""

    list_display = ("momento", "nota", "peso", "objetivo",
                    "exame", "avaliador", "projeto", "alocacao")
    ordering = ("momento",)
    list_filter = ("exame", "projeto__ano", "projeto__semestre")
    search_fields = ["projeto__titulo_final", "projeto__proposta__titulo",
                     "alocacao__aluno__user__username", "projeto__proposta__organizacao__sigla"]


@admin.register(Reprovacao)
class ReprovacaoAdmin(admin.ModelAdmin):
    """Informações das Reprovações."""

    list_display = ("alocacao", "nota",)
    search_fields = ["alocacao__aluno__user__username",]


@admin.register(Observacao)
class ObservacaoAdmin(admin.ModelAdmin):
    """Informações das Observações."""

    list_display = ("momento", "exame", "avaliador", "projeto", "alocacao")
    ordering = ("momento",)
    list_filter = ("exame", )
    search_fields = ["projeto__titulo_final", "projeto__proposta__titulo", "alocacao__aluno__user__username"]
    actions = [dup_entrada]


@admin.register(Observacao_Velha)
class Observacao_VelhaAdmin(admin.ModelAdmin):
    """Informações das Observações Velhas."""

    list_display = ("momento", "exame", "avaliador", "projeto", "alocacao")
    ordering = ("momento",)
    list_filter = ("exame", )
    search_fields = ["projeto__titulo_final", "projeto__proposta__titulo", "alocacao__aluno__user__username"]

@admin.register(Recomendada)
class RecomendadaAdmin(admin.ModelAdmin):
    """Disciplinas Recomendas para Estudentes terem cursado para aplicar na Proposta."""

    list_display = ("proposta", "disciplina")
    ordering = ("proposta",)
    search_fields = ["proposta__titulo"]


@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    """Certificados emitidos."""

    list_display = ("data", "usuario", "projeto", "tipo_certificado", )
    ordering = ("data",)
    list_filter = ("tipo_certificado", "data", "projeto__ano", "projeto__semestre",)
    search_fields = ["usuario__username", "projeto__proposta__organizacao__sigla",
                     "projeto__titulo_final", "projeto__proposta__titulo",]


@admin.register(Cursada)
class CursadaAdmin(admin.ModelAdmin):
    """Disciplinas Cursadas."""

    list_display = ("disciplina", "aluno", "nota")


@admin.register(ObjetivosDeAprendizagem)
class ObjetivosDeAprendizagemAdmin(admin.ModelAdmin):
    """Objetivos de Aprendizagem."""

    list_display = ("titulo", "sigla", "data_inicial", "data_final", "ordem")
    actions = [dup_entrada]


@admin.register(Acompanhamento)
class AcompanhamentoAdmin(admin.ModelAdmin):
    """Acompanhamentos intermediários."""

    list_display = ("data", "autor")


@admin.register(AreaDeInteresse)
class AreaDeInteresseAdmin(admin.ModelAdmin):
    """Area De Interesse."""

    list_display = ("area", "usuario", "proposta",)
    #list_filter = ("area", "usuario__aluno__ano", "usuario__aluno__semestre",)
    list_filter = ("area", AnoSemestreFilter)
    search_fields = ["usuario__username", "proposta__organizacao__sigla", "proposta__titulo",]

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    """Area."""

    list_display = ("titulo", "titulo_en", "descricao", "ativa",)
    search_fields = ["area",]

@admin.register(TipoRetorno)
class TipoRetornoAdmin(admin.ModelAdmin):
    """Tipo de Retorno."""
    
    list_display = ("nome", "grupo_de_retorno", "cor",)
    search_fields = ["nome", "descricao",]

admin.site.register(Entidade)       # Para ser preenchido com as entidades estudantis

admin.site.register(PropostaContato)

@admin.register(Desconto)
class DescontoAdmin(admin.ModelAdmin):
    """Descontos nas notas dos estudantes."""
    list_display = ("evento", "reuniao", "projeto", "alocacao", "nota")
    actions = [dup_entrada]

admin.site.register(Reuniao)

@admin.register(ReuniaoParticipante)
class ReuniaoParticipanteAdmin(admin.ModelAdmin):
    """Participantes das Reuniões."""
    list_display = ("reuniao", "participante", "situacao")
    list_filter = ("reuniao__projeto__ano", "reuniao__projeto__semestre",)
    search_fields = ["reuniao__projeto__titulo_final", "participante__user__username",]
    actions = [dup_entrada]

