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

    path('', views.index_documentos, name='index_documentos'), #pagina inicial

    path('tabela_documentos/', views.tabela_documentos, name='tabela_documentos'),

]
