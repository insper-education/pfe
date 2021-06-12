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

    # pagina inicial
    path('',
         views.index_propostas,
         name='index_propostas'),

    path('map_est_proj/',
         views.mapeamento_estudantes_propostas,
         name='mapeamento_estudantes_propostas'),

    path('procura_propostas/',
         views.procura_propostas,
         name='procura_propostas'),

    path('propostas_apresentadas/',
         views.propostas_apresentadas,
         name='propostas_apresentadas'),

    path('proposta_completa/<int:primarykey>',
         views.proposta_completa,
         name='proposta_completa'),

    path('proposta_detalhes/<int:primarykey>',
         views.proposta_detalhes,
         name='proposta_detalhes'),

    path('proposta_editar/<slug:slug>',
         views.proposta_editar,
         name='proposta_editar'),

    path('ajax/validate_alunos/',
         views.validate_alunos,
         name='validate_alunos'),

    path('ajax/link_organizacao/<int:proposta_id>',
         views.link_organizacao,
         name='link_organizacao'),

    path('ajax/link_disciplina/<int:proposta_id>',
         views.link_disciplina,
         name='link_disciplina'),

    path('ajax/remover_disciplina',
         views.remover_disciplina,
         name='remover_disciplina'),

]
