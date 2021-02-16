#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [

    # pagina inicial
    path('',
         views.index_administracao,
         name='index_administracao'),

    path('backup/<str:formato>',
         views.backup,
         name='backup'),

    path('cadastrar_organizacao/',
         views.cadastrar_organizacao,
         name='cadastrar_organizacao'),

    path('cadastrar_usuario/',
         views.cadastrar_usuario,
         name='cadastrar_usuario'),

    path('carrega_arquivo/<str:dado>',
         views.carrega_arquivo,
         name='carrega_arquivo'),

    path('index_carregar/',
         views.index_carregar,
         name='index_carregar'),

    path('definir_datas/',
         views.definir_datas,
         name='definir_datas'),

    path('exportar/',
         views.exportar,
         name='exportar'),

    path('email_backup/',
         views.email_backup,
         name='email_backup'),

    path('emails/',
         views.emails,
         name='emails'),

    # para Ajax somente
    path('emails_semestre/',
         views.emails_semestre,
         name='emails_semestre'),

    # para Ajax somente
    path('emails_projetos/',
         views.emails_projetos,
         name='emails_projetos'),

    path('export/<str:modelo>/<str:formato>',
         views.export,
         name='export'),

    path('propor/',
         views.propor,
         name='propor'),

    path('montar_grupos/',
         views.montar_grupos,
         name='montar_grupos'),

    path('relatorio/<str:modelo>/<str:formato>',
         views.relatorio,
         name='relatorio'),

    path('relatorio_backup/',
         views.relatorio_backup,
         name='relatorio_backup'),

    path('selecionar_orientadores/',
         views.selecionar_orientadores,
         name='selecionar_orientadores'),

    path('servico/',
         views.servico,
         name='servico'),

    path('pre_alocar_estudante/',
         views.pre_alocar_estudante,
         name='pre_alocar_estudante'),

    path('ajax/definir_orientador/',
         views.definir_orientador,
         name='definir_orientador'),

]
