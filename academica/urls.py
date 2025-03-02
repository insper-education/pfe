#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 10 de Abril de 2023
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_academica, name="index_academica"),  # pagina inicial
    path("academica", views.index_academica, name="academica"),
    path("dinamicas_grupos", views.dinamicas_grupos, name="dinamicas_grupos"),
]
