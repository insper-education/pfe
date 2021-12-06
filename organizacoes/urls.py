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

    # pagina inicial
    path('',
         views.index_organizacoes,
         name='index_organizacoes'),

    path('anotacao/<str:organizacao_id>',
         views.anotacao,
         name='anotacao'),

    path('anotacao/<str:organizacao_id>/<str:anotacao_id>/',
         views.anotacao,
         name='anotacao'),

    path('adiciona_documento_org/<str:organizacao_id>',
         views.adiciona_documento_org,
         name='adiciona_documento_org'),

     path('adiciona_documento_proj/<str:projeto_id>',
         views.adiciona_documento_proj,
         name='adiciona_documento_proj'),

    path('carrega_proposta/',
         views.carrega_proposta,
         name='carrega_proposta'),

    path('organizacoes_lista/',
         views.organizacoes_lista,
         name='organizacoes_lista'),

    path('organizacao_completo/<str:org>',
         views.organizacao_completo,
         name='organizacao_completo'),

    path('organizacoes_prospect/',
         views.organizacoes_prospect,
         name='organizacoes_prospect'),

    path('organizacoes_tabela/',
         views.organizacoes_tabela,
         name='organizacoes_tabela'),

    path('parceiro_propostas',
         views.parceiro_propostas,
         name='parceiro_propostas'),

    path('proposta_submissao',
         views.proposta_submissao,
         name='proposta_submissao'),

    path('projeto_feedback',
         views.projeto_feedback,
         name='projeto_feedback'),

    path('seleciona_conexoes/',
         views.seleciona_conexoes,
         name='seleciona_conexoes'),

     path('todos_parceiros/',
         views.todos_parceiros,
         name='todos_parceiros'),

    path('ajax/estrelas/',
         views.estrelas,
         name='estrelas'),

     path('ajax/areas/',
         views.areas,
         name='areas'),


]
