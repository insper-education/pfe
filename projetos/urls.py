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
    path('', views.index_projetos, name='index_projetos'), #pagina inicial

    path('avisos_listar/', views.avisos_listar, name='avisos_listar'),
    path('carrega_bancos/', views.carrega_bancos, name='carrega_bancos'),
    path('certificados_submetidos/', views.certificados_submetidos, name='certificados_submetidos'),
    path('comite/', views.comite, name='comite'),
    path('completo/<int:primakey>', views.projeto_completo, name='completo'), # REMOVER
    path('dinamicas/<str:periodo>', views.dinamicas, name='dinamicas'),
    path('dinamicas/', views.dinamicas_root, name='dinamicas_root'),
    path('distribuicao_areas/', views.distribuicao_areas, name='distribuicao_areas'),
    path('edita_aviso/<int:primakey>', views.edita_aviso, name='edita_aviso'),
    path('graficos/', views.graficos, name='graficos'),
    path('index_operacional/', views.index_operacional, name='index_operacional'),
    path('lista_feedback', views.lista_feedback, name='lista_feedback'),
    path('meuprojeto/', views.meuprojeto, name='meuprojeto'),
    path('migracao/', views.migracao, name='migracao'),
    path('mostra_feedback/<int:feedback_id>', views.mostra_feedback, name='mostra_feedback'),
    path('projeto_completo/<int:primakey>', views.projeto_completo, name='projeto_completo'),
    path('projeto_detalhes/<int:primarykey>', views.projeto_detalhes, name='projeto_detalhes'),
    path('projeto_feedback', views.projeto_feedback, name='projeto_feedback'),
    path('projetos_fechados/', views.projetos_fechados, name='projetos_fechados'),
    path('projetos_lista/<str:periodo>', views.projetos_lista, name='projetos_lista'),
    path('reembolso_pedir/', views.reembolso_pedir, name='reembolso_pedir'),
    path('relatorio/<str:modelo>/<str:formato>', views.relatorio, name='relatorio'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('ajax/validate_aviso/', views.validate_aviso, name='validate_aviso'),

]
