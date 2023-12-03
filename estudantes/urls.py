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

    path('avaliacao_pares/<str:momento>',
         views.avaliacao_pares,
         name='avaliacao_pares'),

    path('encontros_marcar/',
         views.encontros_marcar,
         name='encontros_marcar'),

    path('estudante_feedback',
         views.estudante_feedback,
         name='estudante_feedback'),

    path('estudante_feedback/<str:hashid>',
        views.estudante_feedback_hashid,
        name='estudante_feedback_hashid'),

    path('exames_pesos/',
        views.exames_pesos,
        name='exames_pesos'),

    path('informacoes_adicionais/',
         views.informacoes_adicionais,
         name='informacoes_adicionais'),

    path('minhas_bancas/',
         views.minhas_bancas,
         name='minhas_bancas'),

    path('relato_quinzenal/',
         views.relato_quinzenal,
         name='relato_quinzenal'),

    path('relato_visualizar/<int:id>',
         views.relato_visualizar,
         name='relato_visualizar'),

    path('selecao_propostas/',
         views.selecao_propostas,
         name='selecao_propostas'),

    path('submissao_documento/',
         views.submissao_documento,
         name='submissao_documento'),
         
    path('ajax/opcao_temporaria/',
         views.opcao_temporaria,
         name='opcao_temporaria'),


]
