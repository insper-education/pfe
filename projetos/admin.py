#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Novembro de 2019
"""

from django.contrib import admin

from .models import *

from .support_admin import *

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

    list_display = ("tipo_evento", "projeto", "get_orientador", "get_organizacao", "startDate", "slug",)
    list_filter = ("tipo_evento", "projeto__ano", "projeto__semestre",)
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
    actions = [dup_entrada, dup_entrada_182]
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
    search_fields = ["projeto__titulo_final", "projeto__proposta__titulo", "alocacao__aluno__user__username", "avaliador__first_name", "avaliador__last_name",]
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
    list_display = ("nota", "projeto", "alocacao",)
    list_filter = ("projeto__ano", "projeto__semestre","alocacao__projeto__ano", "alocacao__projeto__semestre",)
    search_fields = ["projeto__titulo_final", "alocacao__aluno__user__username",]
    actions = [dup_entrada]

@admin.register(Reuniao)
class ReuniaoAdmin(admin.ModelAdmin):
    """Reuniões."""
    list_display = ("titulo", "data_hora", "usuario", "travado",)
    list_filter = ("data_hora", "travado",)
    search_fields = ["titulo", "local",]

@admin.register(ReuniaoParticipante)
class ReuniaoParticipanteAdmin(admin.ModelAdmin):
    """Participantes das Reuniões."""
    list_display = ("reuniao", "participante", "situacao")
    list_filter = ("reuniao__projeto__ano", "reuniao__projeto__semestre",)
    search_fields = ["reuniao__projeto__titulo_final", "participante__first_name", "participante__last_name",]
    actions = [dup_entrada]

@admin.register(EncontroParticipante)
class EncontroParticipanteAdmin(admin.ModelAdmin):
    """Participantes dos Encontros."""
    list_display = ("encontro", "participante", "situacao")
    list_filter = ("encontro__projeto__ano", "encontro__projeto__semestre",)
    search_fields = ["encontro__projeto__titulo_final", "participante__username",]
    actions = [dup_entrada]


@admin.register(Cerimonia)
class CerimoniaAdmin(admin.ModelAdmin):
    """Para Cerimonias."""
    list_display = ("atividade", "startDateTime", "endDateTime", "responsavel","location",)
    actions = [dup_entrada, dup_entrada_182]
    ordering = ("-startDateTime",)
    search_fields = ["atividade", "location",]


admin.site.register(TematicaEncontro)
