#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.urls import path
from . import views

urlpatterns = [
    path('alunos_lista/', views.alunos_lista, name='alunos_lista'),
    path('alunos_inscrevendo/', views.alunos_inscrevendo, name='alunos_inscrevendo'),
    path('aluno_detail/<int:primarykey>', views.aluno_detail, name='aluno_detail'),
    path('areas_interesse/', views.areas_interesse, name='areas_interesse'),
    path('perfil/', views.perfil, name='perfil'),
    path('professor_detail/<int:primarykey>', views.professor_detail, name='professor_detail'),
]
