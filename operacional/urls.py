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
    path("",
         views.index_operacional,
         name="index_operacional"),

    path("avisos_listar/",
         views.avisos_listar,
         name="avisos_listar"),

    path("edita_aviso/<int:primarykey>",
         views.edita_aviso,
         name="edita_aviso"),

    path("carregar_certificado/",
         views.carregar_certificado,
         name="carregar_certificado"),

    path("cria_aviso/",
         views.cria_aviso,
         name="cria_aviso"),

    path("deleta_aviso/<int:primarykey>",
         views.deleta_aviso,
         name="deleta_aviso"),

    path("emails/",
         views.emails,
         name="emails"),

    # para Ajax somente
    path("emails_semestre/",
         views.emails_semestre,
         name="emails_semestre"),

    # para Ajax somente
    path("emails_projetos/",
         views.emails_projetos,
         name="emails_projetos"),

    path("plano_aulas/",
         views.plano_aulas,
         name="plano_aulas"),

]
