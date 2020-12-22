#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [

    path('', views.index_organizacoes, name='index_organizacoes'), #pagina inicial

    path('cria_anotacao/<str:login>', views.cria_anotacao, name='cria_anotacao'),

    path('organizacoes_lista/', views.organizacoes_lista, name='organizacoes_lista'),
    path('organizacao_completo/<str:org>', views.organizacao_completo, name='organizacao_completo'),

    path('organizacoes_prospect/', views.organizacoes_prospect, name='organizacoes_prospect'),
    path('organizacoes_tabela/', views.organizacoes_tabela, name='organizacoes_tabela'),

    path('parceiro_propostas', views.parceiro_propostas, name='parceiro_propostas'),

    path('proposta_submissao', views.proposta_submissao, name='proposta_submissao'),

    path('todos_parceiros/', views.todos_parceiros, name='todos_parceiros'),

]
