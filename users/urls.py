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

    path("estudantes_lista/",
         views.estudantes_lista,
         name="estudantes_lista"),

    path("estudantes_notas/",
         views.estudantes_notas,
         name="estudantes_notas"),

    path("estudantes_notas/<str:professor>",
         views.estudantes_notas,
         name="estudantes_notas"),

    path("blackboard_notas/<str:anosemestre>",
         views.blackboard_notas,
         name="blackboard_notas"),

    path("estudantes_objetivos/",
         views.estudantes_objetivos,
         name="estudantes_objetivos"),

    path("estudantes_inscritos/",
         views.estudantes_inscritos,
         name="estudantes_inscritos"),

    path("estudante_detail/<int:primarykey>",
         views.estudante_detail,
         name="estudante_detail"),

    path("contas_senhas/",
         views.contas_senhas,
         name="contas_senhas"),

    path("contas_senhas/<str:edicao>",
         views.contas_senhas,
         name="contas_senhas"),

    path("envia_contas_senhas/",
         views.envia_contas_senhas,
         name="envia_contas_senhas"),


    path("edita_notas/<int:primarykey>",
         views.edita_notas,
         name="edita_notas"),

    path("parceiro_detail/<int:primarykey>",
         views.parceiro_detail,
         name="parceiro_detail"),

    path("perfil/",
         views.perfil,
         name="perfil"),

    path("professor_detail/<int:primarykey>",
         views.professor_detail,
         name="professor_detail"),

    path("user_detail/<int:primarykey>",
         views.user_detail,
         name="user_detail"),

]
