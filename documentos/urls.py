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
         views.index_documentos,
         name='index_documentos'),

    path('certificados_submetidos/',
         views.certificados_submetidos,
         name='certificados_submetidos'),

    path('gerar_certificados/',
         views.gerar_certificados,
         name='gerar_certificados'),

    path('tabela_atas/',
         views.tabela_atas,
         name='tabela_atas'),

    path('tabela_documentos/',
         views.tabela_documentos,
         name='tabela_documentos'),

    path('tabela_seguros/',
         views.tabela_seguros,
         name='tabela_seguros'),

]
