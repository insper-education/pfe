#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [

    path('', views.index_professor, name='index_professor'), #pagina inicial

    path('bancas_criar/', views.bancas_criar, name='bancas_criar'),
    path('bancas_editar/<int:primarykey>', views.bancas_editar, name='bancas_editar'),


    path('banca_ver/<int:primarykey>', views.banca_ver, name='banca_ver'),
    path('bancas_index/', views.bancas_index, name='bancas_index'),
    path('bancas_lista/<str:periodo_projeto>', views.bancas_lista, name='bancas_lista'),
    path('bancas_tabela/', views.bancas_tabela, name='bancas_tabela'),

    path('banca_avaliar/<slug:slug>', views.banca_avaliar, name='banca_avaliar'),

    path('conceitos_obtidos/<int:primarykey>', views.conceitos_obtidos, name='conceitos_obtidos'),

    path('coorientadores_tabela/', views.coorientadores_tabela, name='coorientadores_tabela'),

    path('orientadores_tabela/', views.orientadores_tabela, name='orientadores_tabela'),

    path('resultado_bancas/', views.resultado_bancas, name='resultado_bancas'),

    path('todos_professores/', views.todos_professores, name='todos_professores'),

]
