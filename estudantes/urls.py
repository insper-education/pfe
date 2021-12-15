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
         views.index_estudantes,
         name='index_estudantes'),

    path('areas_interesse/',
         views.areas_interesse,
         name='areas_interesse'),

    path('encontros_marcar/',
         views.encontros_marcar,
         name='encontros_marcar'),

    path('estudante_feedback',
         views.estudante_feedback,
         name='estudante_feedback'),

    path('estudante_feedback',
         views.estudante_feedback,
         name='estudante_feedback'),

    path('estudante_feedback/<str:hashid>',
        views.estudante_feedback_hashid,
        name='estudante_feedback_hashid'),

    path('informacoes_adicionais/',
         views.informacoes_adicionais,
         name='informacoes_adicionais'),

    path('minhas_bancas/',
         views.minhas_bancas,
         name='minhas_bancas'),

    path('selecao_propostas/',
         views.selecao_propostas,
         name='selecao_propostas'),

    path('ajax/opcao_temporaria/',
         views.opcao_temporaria,
         name='opcao_temporaria'),

]
