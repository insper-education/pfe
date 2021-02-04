#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 29 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [

    # pagina inicial
    path('',
         views.index_operacional,
         name='index_operacional'),

    path('avisos_listar/',
         views.avisos_listar,
         name='avisos_listar'),

    path('edita_aviso/<int:primakey>',
         views.edita_aviso,
         name='edita_aviso'),

]
