#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 10 de Setembro de 2025
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_coordenacao, name="index_coordenacao"),  # pagina inicial
    path("coordenacao", views.index_coordenacao, name="coordenacao"),
]
