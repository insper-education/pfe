#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_organizacoes, name="index_organizacoes"),  # pagina inicial
    path("organizacoes/", views.index_organizacoes, name="organizacoes"),
    path("anotacao/", views.anotacao, name="anotacao"),
    path("anotacao/<int:organizacao_id>", views.anotacao, name="anotacao"),
    path("anotacao/<int:organizacao_id>/<int:anotacao_id>/", views.anotacao, name="anotacao"),
    path("adiciona_despesa/", views.adiciona_despesa, name="adiciona_despesa"),
    path("adiciona_despesa/<int:despesa_id>", views.adiciona_despesa, name="adiciona_despesa"),
    path("adiciona_documento/", views.adiciona_documento, name="adiciona_documento"),
    path("edita_documento/<int:documento_id>", views.edita_documento, name="edita_documento"),
    path("adiciona_documento/<int:organizacao_id>", views.adiciona_documento, name="adiciona_documento"),
    path("adiciona_documento/<int:organizacao_id>/<int:projeto_id>", views.adiciona_documento, name="adiciona_documento"),
    path("adiciona_documento/<int:organizacao_id>/<int:projeto_id>/<str:tipo_nome>", views.adiciona_documento, name="adiciona_documento"),
    path("adiciona_documento/<int:organizacao_id>/<int:projeto_id>/<str:tipo_nome>/<int:documento_id>", views.adiciona_documento, name="adiciona_documento"),
    path("adiciona_documento_estudante/<str:tipo_nome>", views.adiciona_documento_estudante, name="adiciona_documento_estudante"),
    path("adiciona_documento_estudante/<str:tipo_nome>/<int:documento_id>", views.adiciona_documento_estudante, name="adiciona_documento_estudante"),
    path("adiciona_documento_tipo/<str:tipo_nome>", views.adiciona_documento_tipo, name="adiciona_documento_tipo"),
    path("organizacoes_lista/", views.organizacoes_lista, name="organizacoes_lista"),
    path("organizacao_completo/", views.organizacao_completo, name="organizacao_completo"),
    path("organizacao_completo/<str:org>", views.organizacao_completo, name="organizacao_completo"),
    path("organizacoes_prospect/", views.organizacoes_prospect, name="organizacoes_prospect"),
    path("organizacoes_projetos/", views.organizacoes_projetos, name="organizacoes_projetos"),
    path("organizacoes_tabela/", views.organizacoes_tabela, name="organizacoes_tabela"),
    path("parceiro_propostas", views.parceiro_propostas, name="parceiro_propostas"),
    path("parceiro_projetos", views.parceiro_projetos, name="parceiro_projetos"),
    path("proposta_submissao", views.proposta_submissao_velho, name="proposta_submissao_velho"),  # Deixar link antigo
    path("projeto_feedback", views.projeto_feedback, name="projeto_feedback"),
    path("seleciona_conexoes/", views.seleciona_conexoes, name="seleciona_conexoes"),
    path("todos_parceiros/", views.todos_parceiros, name="todos_parceiros"),
    path("todos_usuarios/", views.todos_usuarios, name="todos_usuarios"),

    path("ajax/estrelas/", views.estrelas, name="estrelas"),
    path("ajax/areas/", views.areas, name="areas"),
]
