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
         views.index_professor,
         name='index_professor'),

    path('bancas_criar/',
         views.bancas_criar,
         name='bancas_criar'),

    path('bancas_editar/<int:primarykey>',
         views.bancas_editar,
         name='bancas_editar'),

    path('banca_ver/<int:primarykey>',
         views.banca_ver,
         name='banca_ver'),

    path('bancas_index/',
         views.bancas_index,
         name='bancas_index'),

    path('bancas_lista/<str:periodo_projeto>',
         views.bancas_lista,
         name='bancas_lista'),

    path('bancas_tabela/',
         views.bancas_tabela,
         name='bancas_tabela'),

    path('bancas_tabela_completa/',
         views.bancas_tabela_completa,
         name='bancas_tabela_completa'),

    path('banca_avaliar/<slug:slug>',
         views.banca_avaliar,
         name='banca_avaliar'),

    path('conceitos_obtidos/<int:primarykey>',
         views.conceitos_obtidos,
         name='conceitos_obtidos'),

    path('coorientadores_tabela_completa/',
         views.coorientadores_tabela_completa,
         name='coorientadores_tabela_completa'),

    path('coorientadores_tabela/',
         views.coorientadores_tabela,
         name='coorientadores_tabela'),

    path('dinamicas_index/',
         views.dinamicas_index,
         name='dinamicas_index'),

    path('dinamicas_criar/',
         views.dinamicas_criar,
         name='dinamicas_criar'),

    path('dinamicas_editar/<int:primarykey>',
         views.dinamicas_editar,
         name='dinamicas_editar'),

    path('dinamicas_lista/',
         views.dinamicas_lista,
         name='dinamicas_lista'),

    path('objetivos_rubricas/',
         views.objetivos_rubricas,
         name='objetivos_rubricas'),
     
    path('orientadores_tabela/',
         views.orientadores_tabela,
         name='orientadores_tabela'),

    path('orientadores_tabela_completa/',
         views.orientadores_tabela_completa,
         name='orientadores_tabela_completa'),

    path('resultado_projetos/',
         views.resultado_projetos,
         name='resultado_projetos'),

    path('todos_professores/',
         views.todos_professores,
         name='todos_professores'),

]
