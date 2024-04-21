#!/usr/bin/env python
# pylint: disable=C0103

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.urls import path

from organizacoes.views import projeto_feedback

from . import views

urlpatterns = [

    path("",
        views.index_projetos,
        name="index_projetos"),

    # link antigo (remover)
    path("index_projetos/",
        views.index_projetos,
        name="index_antigo"),

    path("analise_notas/",
        views.analise_notas,
        name="analise_notas"),

    path("evolucao_notas/",
        views.evolucao_notas,
        name="evolucao_notas"),

    path("carrega_bancos/",
        views.carrega_bancos,
        name="carrega_bancos"),

    path("comite/",
        views.comite,
        name="comite"),

#   path("completo/<int:primarykey>",
#       views.projeto_completo,
#       name="completo"),  # REMOVER

    path("distribuicao_areas/",
        views.distribuicao_areas,
        name="distribuicao_areas"),

    path("analise_objetivos/",
        views.analise_objetivos,
        name="analise_objetivos"),

    path("evolucao_objetivos/",
        views.evolucao_objetivos,
        name="evolucao_objetivos"),

    path("evolucao_por_objetivo/",
        views.evolucao_por_objetivo,
        name="evolucao_por_objetivo"),

    path("lista_acompanhamento",
        views.lista_acompanhamento,
        name="lista_acompanhamento"),

    path("acompanhamento_view",
        views.acompanhamento_view,
        name="acompanhamento_view"),

    path("bancas_lista",
        views.bancas_lista,
        name="bancas_lista"),

    path("certificacao_falconi",
        views.certificacao_falconi,
        name="certificacao_falconi"),

    path("correlacao_medias_cr",
        views.correlacao_medias_cr,
        name="correlacao_medias_cr"),

    path("editar_projeto/<int:primarykey>",
        views.editar_projeto,
        name="editar_projeto"),

     path("filtro_projetos",
        views.filtro_projetos,
        name="filtro_projetos"),

    path("lista_feedback",
        views.lista_feedback,
        name="lista_feedback"),

    path("lista_feedback_estudantes",
        views.lista_feedback_estudantes,
        name="lista_feedback_estudantes"),

    path("meuprojeto/",
        views.meuprojeto,
        name="meuprojeto"),

    path("mostra_feedback/<int:feedback_id>",
        views.mostra_feedback,
        name="mostra_feedback"),

    path("mostra_feedback_estudante/<int:feedback_id>",
        views.mostra_feedback_estudante,
        name="mostra_feedback_estudante"),

    path("nomes/",
        views.nomes,
        name="nomes"),

    path("projeto_avancado/<int:primarykey>",
        views.projeto_avancado,
        name="projeto_avancado"),

    path("projeto_completo/<int:primarykey>",
        views.projeto_completo,
        name="projeto_completo"),

    path("projeto_detalhes/<int:primarykey>",
        views.projeto_detalhes,
        name="projeto_detalhes"),

    path("projeto_organizacao/<int:primarykey>",
        views.projeto_organizacao,
        name="projeto_organizacao"),

    path("projetos_fechados/",
        views.projetos_fechados,
        name="projetos_fechados"),

    path("projetos_lista",
        views.projetos_lista,
        name="projetos_lista"),

    path("projetos_vs_propostas",
        views.projetos_vs_propostas,
        name="projetos_vs_propostas"),

    path("reembolso_pedir/",
        views.reembolso_pedir,
        name="reembolso_pedir"),

    path("ajax/validate_aviso/",
        views.validate_aviso,
        name="validate_aviso"),

    path("reenvia_avisos/",
        views.reenvia_avisos,
        name="reenvia_avisos"),
    
    path("upload_pasta_projeto/<int:projeto_id>",
        views.upload_pasta_projeto,
        name="upload_pasta_projeto"),

]