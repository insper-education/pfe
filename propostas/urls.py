#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_propostas, name="index_propostas"),  # pagina inicial
    path("propostas", views.index_propostas, name="propostas"),
    path("carrega_proposta/", views.carrega_proposta, name="carrega_proposta"),
    path("map_est_proj/", views.mapeamento_estudantes_propostas, name="mapeamento_estudantes_propostas"),
    path("procura_propostas/", views.procura_propostas, name="procura_propostas"),
    path("propostas_apresentadas/", views.propostas_apresentadas, name="propostas_apresentadas"),
    path("propostas_lista/", views.propostas_lista, name="propostas_lista"),
    path("proposta_completa/<int:primarykey>", views.proposta_completa, name="proposta_completa"),
    path("proposta_detalhes/<int:primarykey>", views.proposta_detalhes, name="proposta_detalhes"),
    path("proposta_submissao", views.proposta_editar, name="proposta_submissao"),
    path("proposta_editar/<slug:slug>", views.proposta_editar, name="proposta_editar"),
    path("proposta_remover/<slug:slug>", views.proposta_remover, name="proposta_remover"),
    path("projeto_criar/<int:proposta_id>", views.projeto_criar, name="projeto_criar"),
    path("publicar_propostas/", views.publicar_propostas, name="publicar_propostas"),

    path("ajax/validate_alunos/", views.validate_alunos, name="validate_alunos"),
    path("ajax/link_organizacao/<int:proposta_id>", views.link_organizacao, name="link_organizacao"),
    path("ajax/link_disciplina/<int:proposta_id>", views.link_disciplina, name="link_disciplina"),
    path("ajax/remover_disciplina", views.remover_disciplina, name="remover_disciplina"),
    path("ajax_proposta/", views.ajax_proposta, name="ajax_proposta"),    
    path("ajax_proposta/<int:primarykey>", views.ajax_proposta, name="ajax_proposta"),
    path("ajax_proposta_pergunta/<int:primarykey>", views.ajax_proposta_pergunta, name="ajax_proposta_pergunta"),
    path("ajax_proposta_resposta/<int:primarykey>", views.ajax_proposta_resposta, name="ajax_proposta_resposta"),
]
