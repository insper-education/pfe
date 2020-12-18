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

    path('', views.index_estudantes, name='index_estudantes'), #pagina inicial

    path('areas_interesse/', views.areas_interesse, name='areas_interesse'),

    path('encontros_marcar/', views.encontros_marcar, name='encontros_marcar'),

    path('informacoes_adicionais/', views.informacoes_adicionais, name='informacoes_adicionais'),

    path('minhas_bancas/', views.minhas_bancas, name='minhas_bancas'),

    path('selecao_propostas/', views.selecao_propostas, name='selecao_propostas'),

    #path('submissao/', views.submissao, name='submissao'),   #informacoes_adicionais
]
