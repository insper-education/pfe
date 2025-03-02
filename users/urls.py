#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.urls import path
from . import views

urlpatterns = [
    path("blackboard_notas/<str:anosemestre>", views.blackboard_notas, name="blackboard_notas"),
    path("contas_senhas/", views.contas_senhas, name="contas_senhas"),
    path("contas_senhas/<str:edicao>", views.contas_senhas, name="contas_senhas"),
    path("converte_opcoes/<int:ano>/<int:semestre>", views.converte_opcoes, name="converte_opcoes"),
    path("edita_notas/<int:primarykey>", views.edita_notas, name="edita_notas"),
    path("envia_contas_senhas/", views.envia_contas_senhas, name="envia_contas_senhas"),
    path("estudante_detail/<int:primarykey>", views.estudante_detail, name="estudante_detail"),
    path("estudante_detail/", views.estudante_detail, name="estudante_detail"),
    path("estudantes_inscritos/", views.estudantes_inscritos, name="estudantes_inscritos"),
    path("estudantes_lista/", views.estudantes_lista, name="estudantes_lista"),
    path("estudantes_notas/", views.estudantes_notas, name="estudantes_notas"),
    path("estudantes_notas/<str:professor>", views.estudantes_notas, name="estudantes_notas"),
    path("estudantes_objetivos/", views.estudantes_objetivos, name="estudantes_objetivos"),
    path("parceiro_detail/", views.parceiro_detail, name="parceiro_detail"),
    path("parceiro_detail/<int:primarykey>", views.parceiro_detail, name="parceiro_detail"),
    path("perfil/", views.perfil, name="perfil"),
    path("professor_detail/<int:primarykey>", views.professor_detail, name="professor_detail"),
    path("projeto_user/", views.projeto_user, name="projeto_user"),
    path("projetos_objetivos/", views.projetos_objetivos, name="projetos_objetivos"),
    path("user_detail", views.user_detail, name="user_detail"),
    path("user_detail/<int:primarykey>", views.user_detail, name="user_detail"),
]
