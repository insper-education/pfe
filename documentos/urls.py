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
    path("", views.index_documentos, name="index_documentos"),  # pagina inicial
    path("biblioteca_link/", views.biblioteca_link, name="biblioteca_link"),
    path("biblioteca_link/<int:primarykey>", views.biblioteca_link, name="biblioteca_link"),
    path("certificados_submetidos/", views.certificados_submetidos, name="certificados_submetidos"),
    path("certificados_submetidos/<str:edicao>", views.certificados_submetidos, name="certificados_submetidos"),
    path("certificados_submetidos/<str:edicao>/<str:tipos>", views.certificados_submetidos, name="certificados_submetidos"),
    path("certificados_submetidos/<str:edicao>/<str:tipos>/<int:gerados>", views.certificados_submetidos, name="certificados_submetidos"),
    path("contratos_assinados/", views.contratos_assinados, name="contratos_assinados"),
    path("documentos", views.index_documentos, name="documentos"),
    path("duplicar_publicar/<int:relatorio_id>/", views.duplicar_publicar, name="duplicar_publicar"),
    path("exibir_ocultar_notas/", views.exibir_ocultar_notas, name="exibir_ocultar_notas"),
    path("exportar_documentos_projetos/", views.exportar_documentos_projetos, name="exportar_documentos_projetos"),
    path("gerar_certificados/", views.gerar_certificados, name="gerar_certificados"),
    path("materias_midia/", views.materias_midia, name="materias_midia"),
    path("relatorios_publicos/", views.relatorios_publicos, name="relatorios_publicos"),
    path("relatorios_publicos/<str:edicao>", views.relatorios_publicos, name="relatorios_publicos"),
    path("selecao_geracao_certificados/", views.selecao_geracao_certificados, name="selecao_geracao_certificados"),
    path("tabela_atas/", views.tabela_atas, name="tabela_atas"),
    path("tabela_documentos/", views.tabela_documentos, name="tabela_documentos"),
    path("tabela_imagens/", views.tabela_imagens, name="tabela_imagens"),
    path("tabela_seguros/", views.tabela_seguros, name="tabela_seguros"),
]
