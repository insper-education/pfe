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

    path('coorientadores_tabela/', views.coorientadores_tabela, name='coorientadores_tabela'),

    path('professores_tabela/', views.professores_tabela, name='professores_tabela'),

]
