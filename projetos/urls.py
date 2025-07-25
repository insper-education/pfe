#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_projetos, name="index_projetos"),
    path("projetos", views.index_projetos, name="projetos"),
    path("acompanhamento_view", views.acompanhamento_view, name="acompanhamento_view"),
    path("analise_notas/", views.analise_notas, name="analise_notas"),
    path("analise_objetivos/", views.analise_objetivos, name="analise_objetivos"),
    path("bancas_tabela_agenda", views.bancas_tabela_agenda, name="bancas_tabela_agenda"),
    path("carrega_bancos/", views.carrega_bancos, name="carrega_bancos"),
    path("certificacao_falconi",views.certificacao_falconi, name="certificacao_falconi"),
    path("comite/", views.comite, name="comite"),
    path("correlacao_medias_cr", views.correlacao_medias_cr, name="correlacao_medias_cr"),
    path("cria_reuniao/", views.reuniao, name="cria_reuniao"),
    path("edita_reuniao/<int:reuniao_id>", views.reuniao, name="edita_reuniao"),
    path("despesas/", views.despesas, name="despesas"),
    path("distribuicao_areas/", views.distribuicao_areas, name="distribuicao_areas"),
    path("evolucao_areas/", views.evolucao_areas, name="evolucao_areas"),
    path("editar_projeto/<int:primarykey>", views.editar_projeto, name="editar_projeto"),
    path("evolucao_notas/", views.evolucao_notas, name="evolucao_notas"),
    path("evolucao_objetivos/", views.evolucao_objetivos, name="evolucao_objetivos"),
    path("evolucao_por_objetivo/", views.evolucao_por_objetivo, name="evolucao_por_objetivo"),
    path("filtro_projetos", views.filtro_projetos,name="filtro_projetos"),
    path("interesses_projetos", views.interesses_projetos, name="interesses_projetos"),
    path("lista_acompanhamento", views.lista_acompanhamento, name="lista_acompanhamento"),
    path("lista_feedback", views.lista_feedback, name="lista_feedback"),
    path("lista_feedback_estudantes", views.lista_feedback_estudantes, name="lista_feedback_estudantes"),
    path("meuprojeto/", views.meuprojeto, name="meuprojeto"),
    path("meuprojeto/<int:primarykey>", views.meuprojeto, name="meuprojeto"),
    path("mostra_feedback/<int:feedback_id>", views.mostra_feedback, name="mostra_feedback"),
    path("mostra_feedback_estudante/<int:feedback_id>", views.mostra_feedback_estudante,name="mostra_feedback_estudante"),
    path("nomes/", views.nomes, name="nomes"),
    path("projeto_avancado/<int:primarykey>", views.projeto_avancado, name="projeto_avancado"),
    path("projeto_infos/<int:primarykey>", views.projeto_infos, name="projeto_infos"),
    path("projetos_fechados/", views.projetos_fechados, name="projetos_fechados"),
    path("projetos_lista", views.projetos_lista, name="projetos_lista"),
    path("projetos_lista_completa", views.projetos_lista_completa, name="projetos_lista_completa"),
    path("projetos_vs_propostas", views.projetos_vs_propostas, name="projetos_vs_propostas"),
    path("prop_por_opcao/", views.prop_por_opcao, name="prop_por_opcao"),
    path("reembolso_pedir/", views.reembolso_pedir, name="reembolso_pedir"),
    path("reenvia_avisos/", views.reenvia_avisos, name="reenvia_avisos"),
    path("reunioes", views.reunioes, name="reunioes"),
    path("reunioes/<str:todos>", views.reunioes, name="reunioes"),
    path("upload_estudantes_projeto/<int:projeto_id>", views.upload_estudantes_projeto, name="upload_estudantes_projeto"),

    path("ajax/validate_aviso/", views.validate_aviso, name="validate_aviso"),

    # Brincadeira com estudantes    
    path("grupos_formados/", views.grupos_formados, name="grupos_formados"),

]
